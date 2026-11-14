Feature: The executive cut keeps numbers inside their own scope
  The executive cut (_sample_exec) turns on strict_facts: every number spoken or shown
  in a scene must come from a fact the scene itself declares, and every such fact must
  state its scope (which model or which part the number applies to).

  Background:
    Given the executive script and fact table

  Scenario: The executive script passes all checks
    When I validate the script
    Then there are no errors
    And the estimated length is from 60 to 90 seconds
    And the Flesch-Kincaid grade level is 8 or lower

  Scenario: A screen number from outside this scene's facts is rejected
    When the timer card of scene "e03" says "Whole model by hand: 6–12 h"
    And I validate the script
    Then an error for "e03/internal" mentions "6"

  Scenario: A narration number from outside this scene's facts is rejected
    When scene "e03" narration is "Here is one of our 35 parts. For this part, that took about four minutes."
    And I validate the script
    Then an error for "e03" mentions "35"

  Scenario: A fact without a scope is rejected
    When the fact "sheet_metal_parts" has no scope
    And I validate the script
    Then an error for "e04" mentions "scope"
