Feature: User Authentication
  As a user
  I want to be able to log in to the application
  So that I can access my dashboard and tools

  Background:
    Given I am on the login page

  @smoke @regression
  Scenario: Successful login with valid credentials
    When I enter username "testuser"
    And I enter password "password123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message containing "Welcome, testuser"

  @regression
  Scenario: Failed login with invalid credentials
    When I enter username "invaliduser"
    And I enter password "wrongpassword"
    And I click the login button
    Then I should see an error message "Invalid credentials"
    And I should remain on the login page

  @validation
  Scenario Outline: Login form validation
    When I leave the <field> field empty
    And I click the login button
    Then I should see a validation error "<error>"

    Examples:
      | field    | error                    |
      | username | Username is required     |
      | password | Password is required     |

  @security
  Scenario: Password visibility toggle
    When I enter password "mysecretpassword"
    Then the password should be masked
    When I click the show password toggle
    Then the password should be visible
    When I click the show password toggle again
    Then the password should be masked again
