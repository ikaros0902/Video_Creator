Feature: Environment check
  The pipeline needs local tools. "vc doctor" reports each tool and how to fix a missing one.

  Scenario: A missing tool is reported with a fix
    Given the tool "ffmpeg" cannot be found
    When I check the tool "ffmpeg"
    Then the status is "MISSING"
    And the result shows a fix

  Scenario: A missing required item fails the check
    Given the check results contain a required item that failed
    When I run "vc doctor"
    Then the exit code is 1

  Scenario: A failed optional item does not fail the check
    Given the check results contain only an optional item that failed
    When I run "vc doctor"
    Then the exit code is 0

  Scenario Outline: Python version range
    When I check Python version <major>.<minor>
    Then the status is "<status>"

    Examples:
      | major | minor | status  |
      | 3     | 9     | MISSING |
      | 3     | 11    | OK      |
      | 3     | 15    | MISSING |

  Scenario Outline: Node version text is parsed
    When I parse the version text "<text>"
    Then the major version is <major>

    Examples:
      | text     | major |
      | v26.13.0 | 26    |
      | v18.20.4 | 18    |

  Scenario: Hardware GPU encoders are reported by vc.media
    When I inspect detected FFmpeg GPU encoders
    Then every detected encoder is a known hardware H264 codec
