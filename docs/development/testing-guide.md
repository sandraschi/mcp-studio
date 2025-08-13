# MCP Studio Testing Guide

This document provides a comprehensive overview of the testing tools, strategies, and best practices used in the MCP Studio project.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Unit Testing](#unit-testing)
3. [End-to-End Testing with Cypress](#end-to-end-testing-with-cypress)
4. [Behavior-Driven Development with Cucumber](#behavior-driven-development-with-cucumber)
5. [Test Data Management](#test-data-management)
6. [Custom Commands and Utilities](#custom-commands-and-utilities)
7. [Continuous Integration](#continuous-integration)
8. [Running Tests](#running-tests)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Testing Strategy

MCP Studio employs a multi-layered testing approach:

- **Unit Tests**: Test individual components and services in isolation
- **Integration Tests**: Verify interactions between components
- **E2E Tests**: Test complete user flows in a real browser environment
- **API Tests**: Validate API contracts and behavior
- **Visual Regression Tests**: Ensure UI consistency

## Unit Testing

### Tools
- **Framework**: [Jest](https://jestjs.io/)
- **Assertions**: Built-in Jest assertions
- **Mocking**: Jest's built-in mocking capabilities
- **Test Runners**: Jest CLI

### File Naming Convention
- Test files should be named with `.spec.ts` or `.test.ts` suffix
- Place test files next to the code they test
- For components, use `.component.spec.ts`
- For services, use `.service.spec.ts`

### Example Unit Test

```typescript
describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthService]
    });
    
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should login successfully', () => {
    const mockResponse = { token: 'test-token' };
    
    service.login('test@example.com', 'password').subscribe(response => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne('/api/auth/login');
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
  });
});
```

## End-to-End Testing with Cypress

### Key Features
- Real-time reloads
- Automatic waiting
- Network traffic control
- Screenshots and videos
- Cross-browser testing

### Project Structure

```
frontend/
  cypress/
    e2e/
      features/               # Gherkin feature files
      step_definitions/       # Step definitions
      support/               
        commands.ts          # Custom commands
        e2e.ts               # Global setup/teardown
    fixtures/                # Test data
      user.json
      executions.json
    screenshots/             # Test failure screenshots
    videos/                  # Test recordings
```

## Behavior-Driven Development with Cucumber

### Gherkin Syntax

```gherkin
Feature: User Authentication
  As a user
  I want to log in to the application
  So that I can access my dashboard

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter username "testuser"
    And I enter password "password123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message containing "Welcome, testuser"
```

### Step Definitions

```typescript
import { Given, When, Then } from '@badeball/cypress-cucumber-preprocessor';

Given('I am on the login page', () => {
  cy.visit('/login');
  cy.get('h1').should('contain', 'Sign In');
});

When('I enter username {string}', (username: string) => {
  cy.get('input[formControlName="username"]').type(username);
});
```

## Test Data Management

### Fixtures
- Store test data in JSON files under `cypress/fixtures/`
- Use descriptive names (e.g., `user.json`, `executions.json`)
- Keep data realistic but minimal

### Example Fixture

```json
{
  "id": "1",
  "username": "testuser",
  "email": "test@example.com",
  "role": "user"
}
```

### Using Fixtures

```typescript
beforeEach(() => {
  cy.fixture('user.json').as('userData');
  cy.fixture('executions.json').as('executions');
});

it('should display user data', function() {
  const { username, email } = this.userData;
  // Test using the fixture data
});
```

## Custom Commands and Utilities

### Custom Commands

```typescript
// cypress/support/commands.ts

declare global {
  namespace Cypress {
    interface Chainable {
      login(username: string, password: string): Chainable<void>;
      getByTestId(testId: string): Chainable<JQuery<HTMLElement>>;
    }
  }
}

Cypress.Commands.add('login', (username, password) => {
  cy.visit('/login');
  cy.get('input[formControlName="username"]').type(username);
  cy.get('input[formControlName="password"]').type(password, { log: false });
  cy.get('button[type="submit"]').click();
});

Cypress.Commands.add('getByTestId', (testId) => {
  return cy.get(`[data-testid="${testId}"]`);
});
```

### Custom Assertions

```typescript
// cypress/support/assertions.ts

chai.use((chai, utils) => {
  chai.Assertion.addMethod('visibleAndContain', function(text: string) {
    const $element = this._obj;
    
    this.assert(
      $element.is(':visible') && $element.text().includes(text),
      'expected #{this} to be visible and contain #{exp}',
      'expected #{this} not to be visible and contain #{exp}',
      text
    );
  });
});
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run E2E tests
      run: |
        cd frontend
        npm run test:e2e:ci
      
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: cypress-screenshots
        path: frontend/cypress/screenshots
        retention-days: 7
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run a specific test file
npm test -- path/to/test.spec.ts

# Generate coverage report
npm run test:coverage
```

### E2E Tests

```bash
# Open Cypress Test Runner
npm run cypress:open

# Run all E2E tests headlessly
npm run test:e2e

# Run specific feature file
npm run test:e2e -- --spec "cypress/e2e/features/login.feature"

# Run with specific browser
npm run cypress:run -- --browser chrome
```

## Best Practices

### Test Organization
- Group related tests using `describe` blocks
- Use clear, descriptive test names
- Follow the Arrange-Act-Assert pattern
- Keep tests independent and isolated

### Selector Strategy
- Prefer `data-testid` attributes for stable selectors
- Avoid using implementation details like CSS classes
- Use semantic selectors when possible

### Test Data
- Use factories for complex test data
- Keep test data close to tests
- Clean up test data after tests

### Performance
- Use `cy.intercept()` to mock API responses
- Avoid unnecessary waits with `cy.wait()`
- Use `cy.session()` for login state

## Troubleshooting

### Common Issues

**Test Failing Intermittently**
- Add `cy.wait()` for API calls
- Use `{ timeout: 10000 }` for elements that take time to appear
- Check for race conditions

**Element Not Found**
- Verify the element exists in the DOM
- Check if the element is in an iframe
- Ensure the element is not hidden or covered

**Test Hanging**
- Check for unhandled promises
- Look for infinite loops
- Verify all API calls are mocked

### Debugging

```typescript
// Pause test execution
cy.pause();

// Debug with Chrome DevTools
debugger;

// Log to Cypress command log
cy.log('Debug info', { some: 'data' });

// Take a screenshot
cy.screenshot('test-failed');
```

### Resources
- [Cypress Documentation](https://docs.cypress.io/)
- [Cucumber.js Documentation](https://cucumber.io/docs/installation/javascript/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Library](https://testing-library.com/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
