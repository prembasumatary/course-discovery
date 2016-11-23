var BundleTracker = require('webpack-bundle-tracker'),
    ExtractTextPlugin = require('extract-text-webpack-plugin'),
    path = require('path'),
    webpack = require('webpack'),
    loaders = [
        {
            loader: 'css-loader',
            options: {
                minimize: true
            }
        },
        {
            loader: 'sass-loader',
            options: {
                includePaths: [path.resolve('./static/sass/')]
            }
        }
    ];

module.exports = {
    context: __dirname,

    entry: {
        'base.style': './static/sass/main-ltr.scss',
        'base.style-rtl': './static/sass/main-rtl.scss',
        'query-preview': './static/js/query-preview.js',
        'query-preview.style': './static/sass/query-preview.scss'
    },

    output: {
        path: path.resolve('./static/bundles/'),
        filename: '[name]-[hash].js'
    },

    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery'
        }),
        new ExtractTextPlugin('[name]-[hash].css')
    ],

    module: {
        rules: [
            {
                test: /\.s?css$/,
                loader: ExtractTextPlugin.extract({fallbackLoader: 'style-loader', loader: loaders})
            },
            {
                test: /\.woff2?$/,
                // Inline small woff files and output them below font
                loader: 'url-loader',
                query: {
                    name: 'font/[name]-[hash].[ext]',
                    limit: 5000,
                    mimetype: 'application/font-woff'
                }
            },
            {
                test: /\.(ttf|eot|svg)$/,
                loader: 'file-loader',
                query: {
                    name: 'font/[name]-[hash].[ext]'
                }
            },
            {
                test: require.resolve('datatables.net'),
                loader: 'imports-loader?define=>false'
            },
            {
                test: require.resolve('datatables.net-bs'),
                loader: 'imports-loader?define=>false'
            }
        ]
    },
    resolve: {
        modules: ['../node_modules', 'static/bower_components'],
        extensions: ['.css', '.js', '.scss']
    }
};
