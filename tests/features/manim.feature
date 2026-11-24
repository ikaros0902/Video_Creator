Feature: Manim animations follow the narration
  "vc manim" turns cue words into seconds, renders the scene, and checks that each motion starts on time.

  Background:
    Given the sample script
    And narration audio where every word lasts 0.4 seconds
    And the timeline is built

  Scenario: Cue words become seconds inside the scene
    When I make the cue file of scene "s04" for "main"
    Then the cue "step" is at the time of the word "step"
    And the cue file duration equals the scene length in seconds
    And every cue is inside the scene

  Scenario: A missing cue word is rejected
    Given the cue word of "hem" in scene "s04" is "zebra"
    When I try to make the cue file of scene "s04" for "main"
    Then the cue file is rejected with a message that contains "zebra"

  Scenario Outline: Animation that starts late is measured in frames
    When an animation for a cue at <target> seconds starts at <actual> seconds
    Then it is <late> frames late

    Examples:
      | target | actual | late |
      | 5.0    | 4.85   | 0    |
      | 5.0    | 5.0    | 0    |
      | 5.0    | 5.1    | 3    |
