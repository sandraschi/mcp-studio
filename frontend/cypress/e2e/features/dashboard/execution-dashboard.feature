Feature: Execution Dashboard
  As an authenticated user
  I want to view and manage my tool executions
  So that I can monitor and control my workflows

  Background:
    Given I am logged in as "a regular user"
    And I am on the dashboard page

  @smoke @regression
  Scenario: View execution history
    When I navigate to the executions tab
    Then I should see a list of my recent executions
    And I should see the execution status for each item

  @regression
  Scenario: Filter executions by status
    When I select status filter "Completed"
    Then I should only see executions with status "Completed"
    When I clear all filters
    Then I should see all my executions

  @regression
  Scenario: Search for an execution
    When I search for "test-tool"
    Then I should only see executions containing "test-tool"

  @regression
  Scenario: View execution details
    Given I have at least one execution in the list
    When I click on the first execution
    Then I should see the execution details modal
    And I should see the execution parameters
    And I should see the execution status

  @regression
  Scenario: Cancel a running execution
    Given I have a running execution
    When I click the cancel button for that execution
    Then the execution status should change to "Cancelling"
    And I should see a success message

  @pagination
  Scenario: Paginate through execution history
    Given I have more than 10 executions
    When I go to the next page
    Then I should see the next set of executions
    When I change the page size to 25
    Then I should see 25 executions per page

  @sorting
  Scenario: Sort execution history
    When I sort by "Start Time" in "descending" order
    Then the executions should be sorted by start time in descending order
    When I sort by "Tool Name" in "ascending" order
    Then the executions should be sorted by tool name in ascending order
