Feature: Narration audio is checked and timed with Whisper
  "vc align" reads the TTS audio back, measures the word error rate, and times every narration word.

  Scenario Outline: Numbers and spoken forms match after normalization
    When I compare the reference "<reference>" with the transcript "<transcript>"
    Then the word error rate is <wer>

    Examples:
      | reference                                        | transcript                                     | wer |
      | This video shows version three point oh of a tool. | This video shows version 3.0 of a tool.       | 0   |
      | For 35 parts, it took about 40 seconds.          | For thirty-five parts it took about forty seconds. | 0   |
      | By hand, it takes 6 to 12 hours.                 | By hand it takes six to twelve hours.          | 0   |
      | We call it a midsurface.                         | We call it a mid surface.                      | 0   |

  Scenario: A wrong word raises the error rate and is listed
    When I compare the reference "Then it repairs folds and dents." with the transcript "Then it repairs holes and dents."
    Then the word error rate is above 0.05
    And the difference list contains "folds"

  Scenario: Every narration word gets a time, also when Whisper writes a number differently
    Given the narration "This video shows version 3.0 of a tool." with lexicon "3.0" as "three point oh"
    And Whisper heard "This|video|shows|version|3.0|of|a|tool." with 0.4 seconds per word
    When I align the words
    Then every narration word has a start time and an end time
    And the start times never go backward
    And the word "3.0" starts at 1.6 seconds within 0.01

  Scenario: A word that Whisper missed is placed between its neighbours
    Given the narration "Open the tool and check the settings." with no lexicon
    And Whisper heard "Open|the|tool|check|the|settings." with 0.5 seconds per word
    When I align the words
    Then the word "and" starts at 1.5 seconds within 0.01
    And the start times never go backward

  Scenario: Callout words get the time of their first appearance
    Given the narration "Select the solid bodies. Run the job." with no lexicon
    And Whisper heard "Select|the|solid|bodies.|Run|the|job." with 0.5 seconds per word
    When I align the words
    Then the callout word "Run" starts at 2.0 seconds within 0.01

  Scenario: Captions are short, end at sentences, and are not too brief
    Given the narration "The old tool had three problems. It broke small features, like folded edges and dents, and left holes." with no lexicon
    And Whisper heard each narration word with 0.35 seconds per word
    When I align the words
    And I make captions
    Then no caption is longer than 42 characters
    And no caption crosses a sentence end
    And every caption lasts at least 1.0 second

  Scenario: A long sentence is split into balanced captions
    Given the narration "Next, it copies one outer surface and moves it inward by half the thickness. To simulate a thin metal part, we replace the solid with one surface in the middle. This video shows version 3.0 of a CADValidator tool for sheet metal parts." with no lexicon
    And Whisper heard each narration word with 0.3 seconds per word
    When I align the words
    And I make captions
    Then no caption is longer than 42 characters
    And every caption has at least 3 words
    And no caption ends with "a", "the", "of", or "and" unless the sentence ends there

  Scenario: SRT times use the standard format
    When I format 3725.5 seconds as an SRT time
    Then the SRT time is "01:02:05,500"
