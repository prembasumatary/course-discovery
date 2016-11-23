var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var path = require('path');
var webpack = require('webpack');

module.exports = {
    context: __dirname,

    entry: {
        main: './static/js/main.js',
        'main-rtl': './static/js/main-rtl.js',
        // publisher: './static/js/publisher/index.js',
    },

    output: {
        path: path.resolve('./static/bundles/'),
        filename: '[name]-[hash].js',
    },

    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new ExtractTextPlugin('[name]-[contenthash].css'),
        // new webpack.ProvidePlugin({
        //     $: 'jquery',
        // }),
    ],

    module: {
        loaders: [
            {
                test: /\.s?css$/,
                loader: ExtractTextPlugin.extract('style-loader', 'css-loader?minimize!sass')
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
            }
        ],
    },
    sassLoader: {
        includePaths: [path.resolve('./static/sass/')]
    },
    resolve: {
        modulesDirectories: ['../node_modules', 'static/bower_components'],
        extensions: ['', '.js']
    },
};
