from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend, ElasticsearchSearchEngine, ElasticsearchSearchQuery
from haystack.models import SearchResult

from course_discovery.apps.edx_haystack_extensions.elasticsearch_boost_config import get_elasticsearch_boost_config


class DistinctCountsSearchQuery(ElasticsearchSearchQuery):
    """
    Query class that enables support for queries returning counts based on the unique value of a specified field.
    Must be used in conjunction with the DistinctCountsSearchBackendMixin.
    """

    def __init__(self, *args, **kwargs):
        super(DistinctCountsSearchQuery, self).__init__(*args, **kwargs)

        # If set to the name of an index field, hit and facet counts will be computed using a cardinality
        # aggregation so that each document with a unique value for that field is only counted once.
        self.distinct_counts_by = None
        self._distinct_hit_count = 0

    def build_params(self, *args, **kwargs):
        params = super(DistinctCountsSearchQuery, self).build_params(*args, **kwargs)
        if self.distinct_counts_by:
            params['distinct_counts_by'] = self.distinct_counts_by
        return params

    def _clone(self, *args, **kwargs):
        clone = super(DistinctCountsSearchQuery, self)._clone(*args, **kwargs)
        clone.distinct_counts_by = self.distinct_counts_by
        return clone

    def run(self, spelling_query=None, **kwargs):
        """Builds and executes the query. Returns a list of search results."""
        final_query = self.build_query()
        search_kwargs = self.build_params(spelling_query, **kwargs)

        if kwargs:
            search_kwargs.update(kwargs)

        results = self.backend.search(final_query, **search_kwargs)
        self._results = results.get('results', [])
        self._hit_count = results.get('hits', 0)
        self._distinct_hit_count = results.get('distinct_hits', 0)
        self._facet_counts = self.post_process_facets(results)
        self._spelling_suggestion = results.get('spelling_suggestion', None)


class DistinctCountsSearchBackendMixin(object):
    """
    Mixin that enables support for queries returning counts based on the unique value of a specified field.
    """

    # Override of ElasticsearchSearchBackend.search to add support for distinct_counts_by param.
    # All of this code copied line by line from haystack/backends/elasticsearch_backend.py except
    # for the call to _process_results.
    def search(self, query_string, **kwargs):
        if len(query_string) == 0:
            return {
                'results': [],
                'hits': 0,
            }

        if not self.setup_complete:
            self.setup()

        search_kwargs = self.build_search_kwargs(query_string, **kwargs)
        search_kwargs['from'] = kwargs.get('start_offset', 0)

        order_fields = set()
        for order in search_kwargs.get('sort', []):
            for key in order.keys():
                order_fields.add(key)

        geo_sort = '_geo_distance' in order_fields

        end_offset = kwargs.get('end_offset')
        start_offset = kwargs.get('start_offset', 0)
        if end_offset is not None and end_offset > start_offset:
            search_kwargs['size'] = end_offset - start_offset

        try:
            raw_results = self.conn.search(body=search_kwargs,
                                           index=self.index_name,
                                           doc_type='modelresult',
                                           _source=True)
        except elasticsearch.TransportError as e:
            if not self.silently_fail:
                raise

            self.log.error("Failed to query Elasticsearch using '%s': %s", query_string, e, exc_info=True)
            raw_results = {}

        return self._process_results(raw_results,
                                     highlight=kwargs.get('highlight'),
                                     result_class=kwargs.get('result_class', SearchResult),
                                     distance_point=kwargs.get('distance_point'),
                                     geo_sort=geo_sort,
                                     distinct_counts_by=kwargs.get('distinct_counts_by'))

    def build_search_kwargs(self, *args, **kwargs):
        kwargs = dict(kwargs)
        distinct_counts_by = kwargs.get('distinct_counts_by')
        if 'distinct_counts_by' in kwargs:
            del kwargs['distinct_counts_by']

        search_kwargs = super(DistinctCountsSearchBackendMixin, self).build_search_kwargs(*args, **kwargs)

        if distinct_counts_by:
            distinct_count_agg_name = self._get_distinct_count_agg_name(distinct_counts_by)
            aggregations = {distinct_count_agg_name: {'cardinality': {'field': distinct_counts_by}}}

            if search_kwargs.get('facets'):
                for facet_name, facet_config in search_kwargs['facets'].items():
                    new_facet = self._convert_facet_to_aggregation(facet_config)
                    new_facet['aggs'] = {distinct_count_agg_name: {'cardinality': {'field': distinct_counts_by}}}
                    aggregations[facet_name] = new_facet
                del search_kwargs['facets']

            search_kwargs['aggs'] = aggregations

        return search_kwargs

    def _get_distinct_count_agg_name(self, distinct_counts_by_field):
         return 'distinct_{}'.format(distinct_counts_by_field)

    def _convert_facet_to_aggregation(self, facet_config):
        # Only allow the simplest of facet types to be converted for now.
        if len(facet_config.keys()) != 1:
            raise RuntimeError('Facet config expected to have exactly 1 key')
        elif 'terms' in facet_config:
            return self._convert_terms_facet_to_aggregation(facet_config)
        elif 'query' in facet_config:
            return self._convert_query_facet_to_aggregation(facet_config)
        else:
            raise RuntimeError('Cannot convert unsupported facet type to aggregation')

    def _convert_terms_facet_to_aggregation(self, facet_config):
        supported_options = {'field', 'size'}
        for option, value in facet_config['terms'].items():
            if option not in supported_options:
                raise RuntimeError('Cannot convert terms facet to aggregation: Unsupported option')

        # If 'field' and 'size' are the only options present in the config, we shouldn't need to do anything
        # to convert to an aggregation.
        return facet_config

    def _convert_query_facet_to_aggregation(self, facet_config):
        if len(facet_config['query'].keys()) != 1 or 'query_string' not in facet_config['query']:
            raise RuntimeError('Cannot convert query facet to aggregation: Unsupported options')

        if len(facet_config['query']['query_string'].keys()) != 1 or 'query' not in facet_config['query']['query_string']:
            raise RuntimeError('Cannot convert query facet to aggregation: Unsupported query_string option')

        # To convert a query facet to an aggregation, all we need to do is wrap it in a filter.
        return {'filter': facet_config}

    def _process_results(self, raw_results, **kwargs):
        kwargs = dict(kwargs)
        distinct_counts_by = kwargs.get('distinct_counts_by')
        if 'distinct_counts_by' in kwargs:
            del kwargs['distinct_counts_by']

        results = super(DistinctCountsSearchBackendMixin, self)._process_results(raw_results, **kwargs)
        if distinct_counts_by:
            aggs = raw_results['aggregations']
            distinct_count_agg_name = self._get_distinct_count_agg_name(distinct_counts_by)
            results['distinct_hits'] = aggs[distinct_count_agg_name]['value']

            # All of the remaining aggregations should be for facets
            facets = {'fields': {}, 'dates': {}, 'queries': {}}
            for agg_name, data in aggs.items():
                if agg_name == distinct_count_agg_name:
                    continue
                elif 'buckets' in data:
                    facets['fields'][agg_name] = [(bucket['key'], bucket[distinct_count_agg_name]['value']) for bucket in data['buckets']]
                else:
                    facets['queries'][agg_name] = data[distinct_count_agg_name]['value']

            results['facets'] = facets

        return results

class SimpleQuerySearchBackendMixin(object):
    """
    Mixin for simplifying Elasticsearch queries.

    Uses a basic query string query.
    """
    def build_search_kwargs(self, *args, **kwargs):
        """
        Override default `build_search_kwargs` method to set simpler default search query settings.

        source:
          https://github.com/django-haystack/django-haystack/blob/master/haystack/backends/elasticsearch_backend.py#L254
        Without this override the default is:
          'query_string': {
            'default_field': content_field,
            'default_operator': DEFAULT_OPERATOR,
            'query': query_string,
            'analyze_wildcard': True,
            'auto_generate_phrase_queries': True,
            'fuzzy_min_sim': FUZZY_MIN_SIM,
            'fuzzy_max_expansions': FUZZY_MAX_EXPANSIONS,
          }
        """
        query_string = args[0]
        search_kwargs = super(SimpleQuerySearchBackendMixin, self).build_search_kwargs(*args, **kwargs)

        simple_query = {
            'query': query_string,
            'analyze_wildcard': True,
            'auto_generate_phrase_queries': True,
        }

        # https://www.elastic.co/guide/en/elasticsearch/reference/1.7/query-dsl-function-score-query.html
        function_score_config = get_elasticsearch_boost_config()['function_score']
        function_score_config['query'] = {
            'query_string': simple_query
        }

        function_score = {
            'function_score': function_score_config
        }

        if search_kwargs['query'].get('filtered', {}).get('query'):
            search_kwargs['query']['filtered']['query'] = function_score
        elif search_kwargs['query'].get('query_string'):
            search_kwargs['query'] = function_score

        return search_kwargs


class NonClearingSearchBackendMixin(object):
    """
    Mixin that prevents indexes from being cleared.

    Inherit this class if you would prefer, for example, to create a new index when you rebuild indexes rather than
    clearing/updating indexes in place as Haystack normally does.
    """

    def clear(self, models=None, commit=True):  # pylint: disable=unused-argument
        """ Does NOT clear the index.

        Instead of clearing the index, this method logs the fact that the inheriting class does NOT clear
        indexes, advising the user to use the appropriate tools to manually clear the index.
        """
        self.log.info('%s does NOT clear indexes. Indexes should be manually cleared using the APIs/tools appropriate '
                      'for this search service.', self.__class__.__name__)


# pylint: disable=abstract-method
class ConfigurableElasticBackend(ElasticsearchSearchBackend):

    def specify_analyzers(self, mapping, field, index_analyzer, search_analyzer):
        """ Specify separate index and search analyzers for the given field.
          Args:
            mapping (dict): /_mapping attribute on index (maps analyzers to fields)
            field (str): which field to modify
            index_analyzer (str): name of the index_analyzer (should be defined in the /_settings attribute)
            search_analyzer (str): name of the search_analyzer (should be defined in the /_settings attribute)
        """
        # The generic analyzer is used for both if index_analyzer and search_analyzer are not specified
        mapping[field].pop('analyzer')
        mapping[field].update({
            'index_analyzer': index_analyzer,
            'search_analyzer': search_analyzer
        })

    def build_schema(self, fields):
        content_field_name, mapping = super().build_schema(fields)
        # Fields default to snowball analyzer, this keeps snowball functionality, but adds synonym functionality
        snowball_with_synonyms = 'snowball_with_synonyms'
        for field, value in mapping.items():
            if value.get('analyzer') == 'snowball':
                self.specify_analyzers(mapping=mapping, field=field,
                                       index_analyzer=snowball_with_synonyms,
                                       search_analyzer=snowball_with_synonyms)
        # Use the ngram analyzer as the index_analyzer and the lowercase analyzer as the search_analyzer
        # This is necessary to support partial searches/typeahead
        # If we used ngram analyzer for both, then 'running' would get split into ngrams like "ing"
        # and all words containing ing would come back in typeahead.
        self.specify_analyzers(mapping=mapping, field='title_autocomplete',
                               index_analyzer='ngram_analyzer', search_analyzer=snowball_with_synonyms)
        self.specify_analyzers(mapping=mapping, field='authoring_organizations_autocomplete',
                               index_analyzer='ngram_analyzer', search_analyzer=snowball_with_synonyms)
        return (content_field_name, mapping)


# pylint: disable=abstract-method
class EdxElasticsearchSearchBackend(DistinctCountsSearchBackendMixin, SimpleQuerySearchBackendMixin,
                                    NonClearingSearchBackendMixin, ConfigurableElasticBackend):
    pass


class EdxElasticsearchSearchEngine(ElasticsearchSearchEngine):
    backend = EdxElasticsearchSearchBackend
    query = DistinctCountsSearchQuery
