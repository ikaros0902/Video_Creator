Feature: The timeline follows the narration, and the recording fits the timeline
  "vc plan" places every scene in frames. "vc fit" cuts and retimes the recording clips to match.

  Background:
    Given the sample script
    And narration audio where every word lasts 0.4 seconds

  Scenario: Scenes follow each other without gaps or rounding drift
    When I build the timeline
    Then each scene starts on the frame where the previous scene ends
    And the total frame count equals the sum of all scene frame counts
    And each scene start frame equals the rounded running total of scene seconds

  Scenario: Each scene is long enough for its narration
    When I build the timeline
    Then every scene lasts longer than its narration
    And the narration audio of every scene starts inside that scene

  Scenario: Recording clips fill the demo scene exactly
    When I build the timeline
    Then the clips of scene "s05" cover the scene with no gap and no overlap
    And clip 1 of scene "s05" starts on the frame of the word "Second"
    And no clip plays faster than 2.5 times normal speed

  Scenario: A clip that needs more than 2.5 times speed is rejected
    Given clip 0 of scene "s05" uses 20 seconds of source video
    When I try to build the timeline
    Then the timeline is rejected with a message that contains "倍速"

  Scenario: A callout appears on the frame of its word
    When I build the timeline
    Then the callout for "settings" in scene "s05" appears on the frame of that word

  Scenario: Captions stay inside the video
    When I build the timeline
    Then the last caption ends before the last frame of the video

  Scenario: A retimed clip has exactly the planned number of frames
    Given a 4-second test recording at 10 fps
    When I fit a clip of 1.0 to 3.0 seconds into 30 frames
    Then the clip file has 30 frames at 30 fps

  Scenario: A slow clip freezes on its last frame instead of slowing down
    Given a 4-second test recording at 10 fps
    When I fit a clip of 1.0 to 2.0 seconds into 45 frames
    Then the clip file has 45 frames at 30 fps
    And the last 10 frames of the clip are identical

  Scenario: A cropped clip has the crop size
    Given a 4-second test recording at 10 fps
    When I fit a clip of 0.0 to 1.0 seconds into 30 frames with crop 10,20,200,40
    Then the clip file is 200x40 pixels
