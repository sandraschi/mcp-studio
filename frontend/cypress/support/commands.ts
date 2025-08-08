// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

// Add TypeScript support for custom commands
declare global {
  namespace Cypress {
    interface Chainable<Subject = any> {
      /**
       * Custom command to login to the application
       * @example cy.login('test@example.com', 'password123')
       */
      login(username: string, password: string): Chainable<void>;
      
      /**
       * Custom command to check if an element is visible and contains text
       * @example cy.get('h1').shouldBeVisibleAndContain('Welcome')
       */
      shouldBeVisibleAndContain(text: string): Chainable<Subject>;
      
      /**
       * Custom command to wait for the page to be fully loaded
       * @example cy.waitForPageLoad()
       */
      waitForPageLoad(): Chainable<Subject>;
      
      /**
       * Custom command to select DOM element by data-testid attribute
       * @example cy.getByTestId('submit-button')
       */
      getByTestId(testId: string): Chainable<JQuery<HTMLElement>>;
      
      /**
       * Custom command to mock API responses
       * @example cy.mockApiResponse('GET', '/api/tools', { fixture: 'tools.json' })
       */
      mockApiResponse(method: string, url: string, response: any): Chainable<null>;
      
      /**
       * Custom command to clear all mocks
       * @example cy.clearMocks()
       */
      clearMocks(): Chainable<null>;
    }
  }
}

// Command to select elements by data-testid attribute
Cypress.Commands.add('getByTestId', (testId: string) => {
  return cy.get(`[data-testid="${testId}"]`);
});

// Command to mock API responses
Cypress.Commands.add('mockApiResponse', (method: string, url: string, response: any) => {
  cy.intercept(method, url, response);
  return null;
});

// Command to clear all mocks
Cypress.Commands.add('clearMocks', () => {
  cy.intercept('**', (req) => {
    // Default behavior - let the request pass through
    req.req.continue();
  });
  return null;
});

// Add TypeScript support for custom assertions
declare global {
  namespace Chai {
    interface Assertion {
      /**
       * Assert that the element has the expected CSS class
       * @example cy.get('button').should('have.class', 'active')
       */
      haveClass(className: string): void;
      
      /**
       * Assert that the element is visible and contains the expected text
       * @example cy.get('h1').should('be.visibleAndContain', 'Welcome')
       */
      visibleAndContain(text: string): void;
    }
  }
}

// Custom Chai assertion for checking if an element is visible and contains text
chai.use((chai, utils) => {
  const assert = chai.assert;
  
  assert.visibleAndContain = function (element: JQuery, text: string, message?: string) {
    new chai.Assertion(element, message).to.exist;
    new chai.Assertion(element).to.be.visible;
    new chai.Assertion(element).to.contain(text);
  };
  
  chai.Assertion.addMethod('visibleAndContain', function (text: string) {
    const $element = this._obj;
    
    this.assert(
      $element.is(':visible') && $element.text().includes(text),
      'expected #{this} to be visible and contain #{exp}',
      'expected #{this} not to be visible and contain #{exp}',
      text
    );
  });
});
