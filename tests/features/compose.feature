Feature: Slide animations and the master timeline are built from the timeline
  "vc hf" writes one HyperFrames project per animated scene. "vc render" passes the timeline to Remotion.

  Background:
    Given the sample script
    And narration audio where every word lasts 0.4 seconds
    And a work folder with dummy slide pictures
    And the timeline is built

  Scenario: Each animated scene becomes a HyperFrames composition with the scene length
    When I build the HyperFrames project of scene "s03" for "main"
    Then the composition id is "s03-main"
    And the composition duration equals the scene length in seconds
    And the timeline is created paused and registered under the composition id

  Scenario: Cards appear when the narration says their word
    When I build the HyperFrames project of scene "s03" for "main"
    Then card 1 appears at the time of the word "eight"
    And card 2 appears at the time of the word "bends"

  Scenario: A single animated scene retains pictures and branding
    When I build the HyperFrames project of every animated scene for "main"
    Then the animated project retains its source image
    And each animated project contains brand logos

  Scenario: Remotion props use paths inside the work folder
    When I build the Remotion props for "main"
    Then every audio path is relative and has no drive letter
    And scene "s06" is a recording with 4 clips
    And an animated scene without a rendered clip uses a placeholder

  Scenario: Each clip uses the size of its own recording
    When I build the Remotion props for "main" with recording sizes "rec01=1912x1020,rec02=1920x1200,rec03=1920x1200"
    Then every clip from "rec02" has the size 1920x1200
    And every clip from "rec01" has the size 1912x1020

  Scenario Outline: Background music stays below the narration
    When the music is <music> LUFS and the narration is <voice> LUFS
    Then during narration the music is 20 dB below the narration
    And during pauses the music is 14 dB below the narration

    Examples:
      | music | voice |
      | -12.4 | -27.4 |
      | -30.0 | -20.0 |

  Scenario: The single Remotion composition supports recordings
    When I build the Remotion props for "main"
    Then the single composition retains recording scenes
