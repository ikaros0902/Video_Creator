Feature: Local creative workspace
  Design sources and style choices remain traceable and reversible.

  Scenario Outline: Save a design brief
    Given a creative project
    When I save a brief with audience "<audience>" and purpose "<purpose>"
    Then the creative operation is "<result>"
    Examples:
      | audience | purpose | result |
      | engineers | explain a workflow | saved |
      |           | explain a workflow | rejected |
      | engineers |                    | rejected |

  Scenario Outline: Import a local reference
    Given a creative project
    When I import a reference of type "<kind>"
    Then the creative operation is "<result>"
    Examples:
      | kind | result |
      | image | saved |
      | missing | rejected |
      | executable | rejected |

  Scenario: Imported sources do not overwrite each other
    Given a creative project
    When I import the same reference twice
    Then both source records preserve their notes and asset bytes

  Scenario Outline: Apply a style choice
    Given a creative project
    When I apply a style with condition "<condition>"
    Then the creative operation is "<result>"
    Examples:
      | condition | result |
      | valid | saved |
      | low contrast | rejected |
      | small text | rejected |

  Scenario: A style change preserves the previous choice
    Given a creative project
    When I apply two valid style choices
    Then the previous style and project settings have backups

  Scenario Outline: Open a style preview
    Given a creative project
    When I preview the scene with condition "<condition>"
    Then the creative operation is "<result>"
    Examples:
      | condition | result |
      | valid | saved |
      | unknown scene | rejected |
      | invalid style | rejected |

  Scenario: A preview does not change production inputs
    Given a creative project
    When I preview a scene that contains HTML markup
    Then the preview preserves the input files and escapes the markup
