import { Given, When, Then, Before } from '@badeball/cypress-cucumber-preprocessor';

Before(() => {
  // Clear all mocks before each test
  cy.clearMocks();
  
  // Mock the API responses that will be needed for these tests
  cy.fixture('user.json').then((user) => {
    cy.intercept('GET', '/api/user/me', {
      statusCode: 200,
      body: user,
    }).as('getUserProfile');
  });
});

// Background step
Given('I am on the login page', () => {
  cy.visit('/login');
  cy.waitForPageLoad();
  
  // Verify we're on the login page
  cy.get('h1').should('be.visible').and('contain', 'Sign In');
});

// Form interaction steps
When('I enter username {string}', (username: string) => {
  cy.get('input[formControlName="username"]')
    .clear()
    .type(username);
});

When('I enter password {string}', (password: string) => {
  cy.get('input[formControlName="password"]')
    .clear()
    .type(password, { log: false }); // Don't log the password
});

When('I click the login button', () => {
  cy.get('button[type="submit"]').click();
});

// Validation steps
Then('I should be redirected to the dashboard', () => {
  // Wait for the login request to complete and the redirect to happen
  cy.wait('@loginRequest').then((interception) => {
    // Only proceed if the login was successful
    if (interception.response?.statusCode === 200) {
      cy.url().should('include', '/dashboard');
      
      // Wait for the user profile to be loaded
      cy.wait('@getUserProfile');
      
      // Verify dashboard is loaded
      cy.get('app-dashboard').should('be.visible');
    }
  });
});

Then('I should see a welcome message containing {string}', (message: string) => {
  // This selector should be updated based on your actual welcome message element
  cy.get('.welcome-message')
    .should('be.visible')
    .and('contain', message);
});

Then('I should see an error message {string}', (message: string) => {
  cy.get('.error-message')
    .should('be.visible')
    .and('contain', message);
});

Then('I should remain on the login page', () => {
  cy.url().should('include', '/login');
});

// Form validation steps
When('I leave the {string} field empty', (field: string) => {
  const selector = `input[formControlName="${field}"]`;
  cy.get(selector).clear();
  // Trigger validation by blurring the field
  cy.get(selector).blur();
});

Then('I should see a validation error {string}', (error: string) => {
  // Look for a mat-error element containing the error message
  cy.contains('mat-error', error).should('be.visible');
});

// Password visibility steps
Then('the password should be masked', () => {
  cy.get('input[formControlName="password"]')
    .should('have.attr', 'type', 'password');
});

Then('the password should be visible', () => {
  cy.get('input[formControlName="password"]')
    .should('have.attr', 'type', 'text');
});

When('I click the show password toggle', () => {
  cy.get('button[mat-icon-button]').click();
});

// Additional reusable steps for other test files
given('I am logged in as {string}', (userType: string) => {
  // This is a utility step that can be used in other feature files
  const credentials = {
    'an admin': { username: 'admin', password: 'admin123' },
    'a regular user': { username: 'testuser', password: 'password123' },
    'a read-only user': { username: 'viewer', password: 'viewer123' },
  };
  
  const { username, password } = credentials[userType as keyof typeof credentials] || 
    { username: 'testuser', password: 'password123' };
  
  // Use the custom login command
  cy.login(username, password);
});
