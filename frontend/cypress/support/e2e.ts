// Import commands.js using ES2015 syntax:
import './commands';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Handle uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // returning false here prevents Cypress from failing the test
  return false;
});

// Add global test hooks
beforeEach(() => {
  // Reset the server state before each test
  // cy.task('db:reset');
  
  // Clear local storage and cookies
  cy.clearLocalStorage();
  cy.clearCookies();
  
  // Mock the API responses
  cy.intercept('GET', '/api/tools', { fixture: 'tools.json' }).as('getTools');
  cy.intercept('GET', '/api/executions*', { fixture: 'executions.json' }).as('getExecutions');
  
  // Mock authentication
  cy.intercept('POST', '/api/auth/login', (req) => {
    const { username, password } = req.body;
    
    if (username === 'testuser' && password === 'password123') {
      req.reply({
        statusCode: 200,
        body: {
          user: {
            id: '1',
            username: 'testuser',
            email: 'test@example.com',
            role: 'user',
            token: 'test-token'
          }
        },
        delay: 100
      });
    } else {
      req.reply({
        statusCode: 401,
        body: { message: 'Invalid credentials' },
        delay: 100
      });
    }
  }).as('loginRequest');
});

// Custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to log in a user
       * @example cy.login('testuser', 'password123')
       */
      login(username: string, password: string): Chainable<void>;
      
      /**
       * Custom command to check if an element is visible and contains text
       * @example cy.get('h1').shouldBeVisibleAndContain('Welcome')
       */
      shouldBeVisibleAndContain(text: string): Chainable<void>;
      
      /**
       * Custom command to wait for the page to be fully loaded
       * @example cy.waitForPageLoad()
       */
      waitForPageLoad(): Chainable<void>;
    }
  }
}

// Custom command to log in a user
Cypress.Commands.add('login', (username: string, password: string) => {
  cy.session([username, password], () => {
    cy.visit('/login');
    
    // Fill in the login form
    cy.get('input[formControlName="username"]').type(username);
    cy.get('input[formControlName="password"]').type(password, { log: false });
    
    // Submit the form
    cy.get('button[type="submit"]').click();
    
    // Wait for the login request to complete
    cy.wait('@loginRequest');
    
    // Verify successful login by checking for dashboard element
    cy.url().should('include', '/dashboard');
  });
});

// Custom command to check if an element is visible and contains text
Cypress.Commands.add('shouldBeVisibleAndContain', { prevSubject: 'element' }, (subject, text) => {
  cy.wrap(subject).should('be.visible').and('contain', text);
});

// Custom command to wait for the page to be fully loaded
Cypress.Commands.add('waitForPageLoad', () => {
  // Wait for Angular to be stable
  cy.window().should('have.property', 'ng');
  
  // Wait for all pending XHR requests to complete
  cy.intercept('**').as('anyRequest');
  cy.wait('@anyRequest', { timeout: 10000 }).then((interception) => {
    // Additional checks can be added here if needed
  });
});
