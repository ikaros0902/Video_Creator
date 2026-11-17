Feature: The script is complete, correct, and plain
  "vc validate" checks script.json against facts.yaml before any audio or video is made.

  Background:
    Given the sample script and fact table

  Scenario: The sample script passes all checks
    When I validate the script
    Then there are no errors
    And the estimated length is from 130 to 170 seconds
    And the Flesch-Kincaid grade level is 8 or lower

  Scenario: A long sentence is rejected
    When scene "s02" narration is "This sentence has far too many words because it keeps going on and on and on without any stop at all here."
    And I validate the script
    Then an error for "s02" mentions "句子超過"

  Scenario: A number without a source is rejected
    When scene "s07" narration is "For 36 sheet metal parts, it took about 40 seconds. By hand, it takes 6 to 12 hours."
    And I validate the script
    Then an error for "s07" mentions "36"

  Scenario: An unconfirmed fact is rejected
    When the fact "batch_runtime" is not confirmed
    And I validate the script
    Then an error for "s07" mentions "尚未確認"

  Scenario: Internal jargon is rejected
    When scene "s04" narration is "Next, it offsets the skin by t/2. Then it repairs folds and dents. Last, it checks that nothing is missing. It has four steps."
    And I validate the script
    Then an error for "s04" mentions "t/2"

  Scenario: The key term must be explained before it is used
    When scene "s01" narration is "This video shows a midsurface tool, version 3.0, for sheet metal parts."
    And I validate the script
    Then an error for "glossary" mentions "midsurface"

  Scenario: The public version cannot use real footage
    When the public visual of scene "s05" uses the internal recording
    And I validate the script
    Then an error for "s05" mentions "public 版不能使用 recording"

  Scenario: The public version cannot use PPT pictures
    When the public visual of scene "s05" adds the picture "slides/images/slide06_pic2.png"
    And I validate the script
    Then an error for "s05" mentions "public 版不能使用 PPT 圖片"

  Scenario: A clip past the end of the recording is rejected
    Given the recording "rec01" is 110.4 seconds long
    And the recording "rec02" is 243.75 seconds long
    And the recording "rec03" is 45.47 seconds long
    When clip 0 of scene "s05" ends at 60.0 seconds
    And I validate the script
    Then an error for "s05/internal" mentions "超過錄影長度"

  Scenario: A callout word must be spoken
    When callout 0 of scene "s05" is linked to the word "Configure"
    And I validate the script
    Then an error for "s05/internal" mentions "Configure"

  Scenario: Sections must follow the agreed order
    When scenes "s03" and "s04" change places
    And I validate the script
    Then an error for "script" mentions "段落順序"
