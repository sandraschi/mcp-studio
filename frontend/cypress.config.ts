import { defineConfig } from 'cypress';
import webpackPreprocessor from '@cypress/webpack-preprocessor';
import { Configuration } from 'webpack';
import { addCucumberPreprocessorPlugin } from '@badeball/cypress-cucumber-preprocessor';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:4200',
    specPattern: '**/*.feature',
    supportFile: 'cypress/support/e2e.ts',
    fixturesFolder: 'cypress/fixtures',
    video: false,
    screenshotOnRunFailure: true,
    viewportWidth: 1920,
    viewportHeight: 1080,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 60000,
    chromeWebSecurity: false,
    retries: {
      runMode: 1,
      openMode: 0
    },
    setupNodeEvents: async (on, config) => {
      // This is required for the preprocessor to be able to generate JSON reports after each run
      await addCucumberPreprocessorPlugin(on, config);
      
      // Webpack configuration
      const webpackOptions: Configuration = {
        resolve: {
          extensions: ['.ts', '.js'],
        },
        module: {
          rules: [
            {
              test: /\.ts$/,
              exclude: [/node_modules/],
              use: [
                {
                  loader: 'ts-loader',
                },
              ],
            },
            {
              test: /\.feature$/,
              use: [
                {
                  loader: '@badeball/cypress-cucumber-preprocessor/webpack',
                  options: config,
                },
              ],
            },
          ],
        },
      };

      on(
        'file:preprocessor',
        webpackPreprocessor({
          webpackOptions,
          webpack: require('webpack'),
        })
      );

      // Make sure to return the config object as it might have been modified by the plugin
      return config;
    },
    env: {
      apiUrl: 'http://localhost:8000/api',
      // Add other environment variables as needed
    },
  },
});
