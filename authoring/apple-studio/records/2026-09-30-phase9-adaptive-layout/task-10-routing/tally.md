## Original sweep (28 rows, Step 1/2 descriptions) (3 runs: run-1, run-2, run-3)

id             expect  pass/3   run1->fired           run2->fired           run3->fired          notes
ad-fire-1      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-2      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   
ad-fire-3      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   
ad-fire-4      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-5      FIRE    1/3      (none)(FAIL)          (none)(FAIL)          apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-6      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns
ad-fire-7      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-8      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-9      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-10     FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   
ad-nofire-1    NOFIRE  0/3      apple-design(FAIL)    apple-design(FAIL)    apple-design(FAIL)   max_turns,max_turns,max_turns
ad-nofire-2    NOFIRE  3/3      (none)(PASS)          (none)(PASS)          (none)(PASS)         max_turns,max_turns,max_turns
ad-nofire-3    NOFIRE  3/3      run(PASS)             run(PASS)             run(PASS)            max_turns,max_turns,max_turns
ad-nofire-4    NOFIRE  3/3      swift-architecture(PASS)  swift-architecture(PASS)  swift-architecture(PASS) 
ad-nofire-5    NOFIRE  3/3      xcode-loop(PASS)      xcode-loop(PASS)      run(PASS)            max_turns,max_turns,max_turns
ad-nofire-6    NOFIRE  3/3      app-release(PASS)     (none)(PASS)          app-release(PASS)    
ar-fire-1      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    max_turns,max_turns,max_turns
ar-fire-2      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    
ar-fire-3      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    
ar-fire-4      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    
ar-fire-5      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    max_turns,max_turns,max_turns
ar-fire-6      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    max_turns,max_turns,max_turns
ar-fire-7      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    
ar-fire-8      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    
ar-nofire-1    NOFIRE  3/3      xcode-loop(PASS)      xcode-loop(PASS)      xcode-loop(PASS)     max_turns,max_turns,max_turns
ar-nofire-2    NOFIRE  3/3      (none)(PASS)          (none)(PASS)          apple-frameworks(PASS) max_turns
ar-nofire-3    NOFIRE  3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ar-nofire-4    NOFIRE  3/3      swift-architecture(PASS)  swift-architecture(PASS)  swift-architecture(PASS) 

Rows not holding (PASS count < 2/3):
  ad-fire-5: 1/3 PASS  fired=['(none)', '(none)', 'apple-design']  notes=['max_turns', 'max_turns', 'max_turns']
  ad-nofire-1: 0/3 PASS  fired=['apple-design', 'apple-design', 'apple-design']  notes=['max_turns', 'max_turns', 'max_turns']

Duo FIRE rows (ad-fire-7, ad-fire-8, ad-fire-9, ad-fire-10):
  ad-fire-7: 3/3 PASS -> HOLDS
  ad-fire-8: 3/3 PASS -> HOLDS
  ad-fire-9: 3/3 PASS -> HOLDS
  ad-fire-10: 3/3 PASS -> HOLDS

## Baseline re-run: ad-fire-5 (3 runs, baseline-ad-fire-5-1, baseline-ad-fire-5-2, baseline-ad-fire-5-3)

  baseline-1: apple-design(PASS)
  baseline-2: apple-design(PASS)
  baseline-3: apple-design(PASS)
  3/3 PASS -> HOLDS at baseline

## Revision round (18 rows: ad-fire-1..10, ad-nofire-1..6, ar-fire-8, ar-nofire-3 — revised apple-design description) (3 runs: run-rev-1, run-rev-2, run-rev-3)

id             expect  pass/3   run1->fired           run2->fired           run3->fired          notes
ad-fire-1      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-2      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   
ad-fire-3      FIRE    2/3      (none)(FAIL)          apple-design(PASS)    apple-design(PASS)   
ad-fire-4      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-5      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-6      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   
ad-fire-7      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-8      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns
ad-fire-9      FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns
ad-fire-10     FIRE    3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   
ad-nofire-1    NOFIRE  2/3      apple-design(FAIL)    (none)(PASS)          (none)(PASS)         max_turns,max_turns
ad-nofire-2    NOFIRE  3/3      xcode-loop(PASS)      (none)(PASS)          (none)(PASS)         max_turns,max_turns,max_turns
ad-nofire-3    NOFIRE  3/3      run(PASS)             run(PASS)             run(PASS)            max_turns,max_turns,max_turns
ad-nofire-4    NOFIRE  3/3      swift-architecture(PASS)  swift-architecture(PASS)  (none)(PASS)         
ad-nofire-5    NOFIRE  3/3      run(PASS)             run(PASS)             xcode-loop(PASS)     max_turns,max_turns,max_turns
ad-nofire-6    NOFIRE  3/3      app-release(PASS)     (none)(PASS)          app-release(PASS)    
ar-fire-8      FIRE    3/3      app-release(PASS)     app-release(PASS)     app-release(PASS)    
ar-nofire-3    NOFIRE  3/3      apple-design(PASS)    apple-design(PASS)    apple-design(PASS)   max_turns,max_turns,max_turns

Rows not holding (PASS count < 2/3):
  (none)

Duo FIRE rows (ad-fire-7, ad-fire-8, ad-fire-9, ad-fire-10):
  ad-fire-7: 3/3 PASS -> HOLDS
  ad-fire-8: 3/3 PASS -> HOLDS
  ad-fire-9: 3/3 PASS -> HOLDS
  ad-fire-10: 3/3 PASS -> HOLDS

