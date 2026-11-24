Feature: Local reference video analysis
  Reference analysis preserves source material and does not use cloud models.

  Scenario: Analyze a valid local video
    Given a local reference video and an isolated analysis tool
    When I analyze the reference video
    Then the analysis contains reports and the source video is unchanged
    And cloud analysis is disabled

  Scenario Outline: Reject unavailable analysis inputs
    Given a local reference video and an isolated analysis tool
    And the analysis input has "<problem>"
    When I analyze the reference video
    Then analysis fails with "<message>"
    Examples:
      | problem       | message          |
      | missing video | local video      |
      | missing tool  | setup-reference  |
      | invalid video | valid video      |

  Scenario: Preserve an existing analysis
    Given a local reference video and an isolated analysis tool
    And an analysis with the same name already exists
    When I analyze the reference video
    Then analysis fails with "already exists"

  Scenario: Reject incomplete tool output
    Given a local reference video and an isolated analysis tool
    And the analysis tool returns incomplete output
    When I analyze the reference video
    Then analysis fails with "required reports"

  Scenario Outline: Report analysis tool failures
    Given a local reference video and an isolated analysis tool
    And the analysis tool has "<problem>"
    When I analyze the reference video
    Then analysis fails with "<message>"
    Examples:
      | problem | message            |
      | failure | exit code 3        |
      | timeout | did not complete   |
