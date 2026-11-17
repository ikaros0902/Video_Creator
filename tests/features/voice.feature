Feature: Narration audio is generated per scene
  "vc voice" makes one WAV file for each scene and reuses files that did not change.

  Background:
    Given the sample script
    And a fake TTS backend

  Scenario: The lexicon changes the spoken text but not the narration
    When I generate the narration audio
    Then the spoken text of scene "s01" contains "CAD Validator"
    And the narration of scene "s01" still contains "CADValidator"

  Scenario: Every scene gets a 48 kHz mono WAV and a recorded duration
    When I generate the narration audio
    Then every scene has a WAV file at 48000 Hz with 1 channel
    And every scene duration in the manifest matches its WAV file

  Scenario: Only the changed scene is generated again
    Given the narration audio was generated once
    When scene "s04" narration is "Version 3.0 works in four steps. Last, it checks that nothing is missing."
    And I generate the narration audio
    Then only scene "s04" is generated again

  Scenario: A different voice generates every scene again
    Given the narration audio was generated once
    When the fake backend voice is "other"
    And I generate the narration audio
    Then all 7 scenes are generated

  Scenario: Silence at the start and end of a scene is trimmed
    Given a WAV file with 0.5 seconds of silence, 1.0 second of tone, and 0.6 seconds of silence
    When I trim the silence
    Then the WAV file lasts 1.16 seconds within 0.02

  Scenario: The preview joins all scenes with a short gap
    When I generate the narration audio
    And I make the preview with a 0.4 second gap
    Then the preview length equals the total scene length plus 7 gaps, within 0.05 seconds
