Feature: Ingest the source material
  The pipeline reads the PPT and the screen recording, so the script author can see the content.

  Scenario: Text, levels, notes, tables, and pictures come out of a PPT
    Given a 3-slide test deck
    When I extract the deck
    Then the result has 3 slides
    And slide 1 has the title "Old Tool Problems"
    And slide 2 has paragraph levels "0,1,1"
    And slide 2 has the notes "Explain the three bottlenecks."
    And slide 3 has 1 picture that exists on disk with size 64x32
    And slide 3 has a table with first row "Setting,Value"

  Scenario: Scene cuts and activity are found in a recording
    Given a 6-second test video with 3 solid-color parts and no audio
    When I analyze the recording with a thumbnail every 1 second
    Then the duration is 6.0 seconds within 0.1
    And 3 scenes are found
    And 6 thumbnails and 1 contact sheet are written
    And activity is found only near 2 and 4 seconds
    And the recording has no audio

  Scenario: Audio level is measured when the recording has sound
    Given a 2-second test video with a sine tone
    When I analyze the recording with a thumbnail every 1 second
    Then the recording has audio with a mean volume above -40 dB
