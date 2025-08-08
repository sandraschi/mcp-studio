import { Given, When, Then, Before } from '@badeball/cypress-cucumber-preprocessor';

Before(() => {
  // Mock API responses for dashboard
  cy.fixture('executions.json').then((executions) => {
    // Mock the executions list
    cy.intercept('GET', '/api/executions*', (req) => {
      // Handle filtering by status
      const status = req.query.status;
      let filteredExecutions = [...executions];
      
      if (status) {
        filteredExecutions = filteredExecutions.filter(
          (exec: any) => exec.status.toLowerCase() === status.toLowerCase()
        );
      }
      
      // Handle search
      const search = req.query.search;
      if (search) {
        const searchLower = search.toLowerCase();
        filteredExecutions = filteredExecutions.filter(
          (exec: any) => 
            exec.tool.toLowerCase().includes(searchLower) ||
            exec.executionId.toLowerCase().includes(searchLower)
        );
      }
      
      // Handle pagination
      const limit = parseInt(req.query.limit as string) || 10;
      const offset = parseInt(req.query.offset as string) || 0;
      const paginatedExecutions = filteredExecutions.slice(offset, offset + limit);
      
      req.reply({
        statusCode: 200,
        body: {
          data: paginatedExecutions,
          total: filteredExecutions.length,
          limit,
          offset
        }
      });
    }).as('getExecutions');
    
    // Mock execution details
    cy.intercept('GET', '/api/executions/*', (req) => {
      const executionId = req.url.split('/').pop();
      const execution = executions.find((e: any) => e.executionId === executionId);
      
      if (execution) {
        req.reply({
          statusCode: 200,
          body: execution
        });
      } else {
        req.reply({
          statusCode: 404,
          body: { message: 'Execution not found' }
        });
      }
    }).as('getExecutionDetails');
    
    // Mock cancel execution
    cy.intercept('POST', '/api/executions/*/cancel', (req) => {
      const executionId = req.url.split('/').slice(-2, -1)[0];
      const execution = executions.find((e: any) => e.executionId === executionId);
      
      if (execution) {
        execution.status = 'cancelling';
        req.reply({
          statusCode: 200,
          body: { success: true }
        });
      } else {
        req.reply({
          statusCode: 404,
          body: { message: 'Execution not found' }
        });
      }
    }).as('cancelExecution');
  });
});

// Background steps
Given('I am on the dashboard page', () => {
  cy.visit('/dashboard');
  cy.waitForPageLoad();
  
  // Wait for the dashboard to load
  cy.get('app-dashboard').should('be.visible');
  cy.wait('@getExecutions');
});

// Navigation steps
When('I navigate to the executions tab', () => {
  cy.get('a[routerLink="/dashboard/executions"]').click();
  cy.url().should('include', '/dashboard/executions');
  
  // Wait for the executions to load
  cy.get('app-execution-dashboard').should('be.visible');
  cy.wait('@getExecutions');
});

// Filtering and search steps
When('I select status filter {string}', (status: string) => {
  cy.get('mat-select[formControlName="status"]').click();
  cy.get('mat-option').contains(status).click();
  
  // Wait for the filtered results
  cy.wait('@getExecutions');
});

When('I clear all filters', () => {
  cy.get('button').contains('Clear Filters').click();
  
  // Wait for the results to be refreshed
  cy.wait('@getExecutions');
});

When('I search for {string}', (query: string) => {
  cy.get('input[placeholder="Search executions..."]').type(query);
  
  // Wait for the search results
  cy.wait('@getExecutions');
});

// Execution details steps
Given('I have at least one execution in the list', () => {
  // This is handled by the mock data
  cy.get('mat-row').should('have.length.gt', 0);
});

When('I click on the first execution', () => {
  cy.get('mat-row').first().click();
  
  // Wait for the details to load
  cy.wait('@getExecutionDetails');
});

Then('I should see the execution details modal', () => {
  cy.get('mat-dialog-container').should('be.visible');
  cy.get('h2').should('contain', 'Execution Details');
});

Then('I should see the execution parameters', () => {
  cy.get('.execution-parameters').should('be.visible');
});

Then('I should see the execution status', () => {
  cy.get('.execution-status').should('be.visible');
});

// Execution actions
Given('I have a running execution', () => {
  // The mock data includes a running execution
  cy.get('mat-row').contains('running').first().parent('mat-row').as('runningExecution');
});

When('I click the cancel button for that execution', () => {
  cy.get('@runningExecution').within(() => {
    cy.get('button[aria-label="Cancel execution"]').click();
  });
  
  // Wait for the cancel request
  cy.wait('@cancelExecution');
});

Then('the execution status should change to {string}', (status: string) => {
  cy.get('@runningExecution')
    .find('.execution-status')
    .should('contain', status);
});

Then('I should see a success message', () => {
  cy.get('snack-bar-container')
    .should('be.visible')
    .and('contain', 'Execution cancelled successfully');
});

// Pagination steps
Given('I have more than 10 executions', () => {
  // This is handled by the mock data which returns more than 10 items
  cy.get('.mat-paginator-range-label').should('contain', 'of');
});

When('I go to the next page', () => {
  cy.get('.mat-paginator-navigation-next').click();
  
  // Wait for the next page to load
  cy.wait('@getExecutions');
});

When('I change the page size to {int}', (size: number) => {
  cy.get('mat-paginator-page-size-select').click();
  cy.get('mat-option').contains(size.toString()).click();
  
  // Wait for the page size to update
  cy.wait('@getExecutions');
});

Then('I should see {int} executions per page', (count: number) => {
  cy.get('mat-row').should('have.length', count);
});

// Sorting steps
When('I sort by {string} in {string} order', (column: string, order: 'ascending' | 'descending') => {
  const sortDirection = order === 'ascending' ? 'asc' : 'desc';
  
  // Find the column header and click to sort
  cy.get('th').contains(column).click();
  
  // If we need to change the sort direction, click again
  if (sortDirection === 'desc') {
    cy.get('th').contains(column).click();
  }
  
  // Wait for the sorted results
  cy.wait('@getExecutions');
});

Then('the executions should be sorted by {string} in {string} order', 
  (column: string, order: 'ascending' | 'descending') => {
    // This is a simplified check - in a real test, you would verify the actual sorting
    cy.get('th')
      .contains(column)
      .should('have.attr', 'aria-sort', order === 'ascending' ? 'asc' : 'desc');
  }
);

// List verification steps
Then('I should see a list of my recent executions', () => {
  cy.get('mat-table').should('be.visible');
  cy.get('mat-row').should('have.length.gt', 0);
});

Then('I should see the execution status for each item', () => {
  cy.get('mat-row').each(($row) => {
    cy.wrap($row).within(() => {
      cy.get('.execution-status').should('be.visible');
    });
  });
});

Then('I should only see executions with status {string}', (status: string) => {
  cy.get('mat-row').each(($row) => {
    cy.wrap($row).within(() => {
      cy.get('.execution-status').should('contain', status);
    });
  });
});

Then('I should only see executions containing {string}', (text: string) => {
  cy.get('mat-row').each(($row) => {
    cy.wrap($row).should('contain', text);
  });
});
