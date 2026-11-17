Feature: Custom styles and camera plans control rendered scenes
  Project settings select validated tokens and deterministic camera motion.
  Unaligned narration anchors keep their fallback timing.
  Explicit camera plans reject scenes with unsupported variants.
  Safe margin tokens control the main title and content positions.
  Main content blocks stay inside both horizontal safe margins.

  Scenario: Style selection changes the generated scene
    Given a title scene with a fixed camera
    When I render the scene with two valid style presets
    Then the palette and surface tokens differ
    And the narration timing stays unchanged

  Scenario: Unsafe or unreadable tokens stop generation
    Given a style with low text contrast or invalid CSS values
    When I validate the style
    Then validation fails with an actionable error

  Scenario: A camera plan controls scene motion
    Given a scene with a valid dolly shot
    When I generate its HyperFrames composition
    Then its paused timeline contains the requested camera transform
    And invalid shot timing fails before generation
