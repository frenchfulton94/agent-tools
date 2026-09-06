/* =============================================================================
   quiz.js — retrieval-practice widget. One question, N choices, immediate
   feedback, no second guess.
   -----------------------------------------------------------------------------
   MARKUP CONTRACT

     <div class="quiz" data-quiz>
       <p class="quiz-prompt">Which file records what a previous run installed?</p>
       <ol class="quiz-choices">
         <li><button type="button" data-correct
                     data-feedback="Its hashes are the ownership test.">
           The record file under .claude
         </button></li>
         <li><button type="button"
                     data-feedback="That one holds the level's default schema.">
           The config file under openspec
         </button></li>
       </ol>
       <p class="quiz-result" role="status" aria-live="polite"></p>
     </div>

   RULES THIS SCRIPT ENFORCES AT RUNTIME (console warnings, never visible):
   - exactly one choice carries data-correct;
   - every choice has the same word count, and character counts within 4 of
     each other. Equal-length answers are the point: a longer or more hedged
     option is a free clue, and a free clue is not retrieval practice.

   The choice order is shuffled on load, so the correct answer's position
   carries no information either, and re-reading a lesson is a fresh test.
   ========================================================================== */

(() => {
	'use strict';

	const WS = /\s+/g;

	const words = (s) => s.trim().split(WS).filter(Boolean).length;
	const chars = (s) => s.replace(WS, ' ').trim().length;

	/** Fisher-Yates, in place. */
	function shuffle(list) {
		for (let i = list.length - 1; i > 0; i -= 1) {
			const j = Math.floor(Math.random() * (i + 1));
			[list[i], list[j]] = [list[j], list[i]];
		}
		return list;
	}

	/**
	 * Warns when the answer set gives away the answer by shape. Authoring aid
	 * only — it never changes what the learner sees, because a lesson that
	 * silently hid a malformed question would be worse than one that renders it.
	 */
	function auditChoices(quiz, buttons) {
		const label = quiz.querySelector('.quiz-prompt')?.textContent?.slice(0, 60) ?? '(unlabelled)';
		const correct = buttons.filter((b) => b.hasAttribute('data-correct'));
		if (correct.length !== 1) {
			console.warn(`[quiz] "${label}…" has ${correct.length} correct choices; expected exactly 1.`);
		}
		const texts = buttons.map((b) => b.textContent ?? '');
		const wordCounts = new Set(texts.map(words));
		if (wordCounts.size > 1) {
			console.warn(`[quiz] "${label}…" choices differ in word count: ${[...wordCounts].join(', ')}.`);
		}
		const charCounts = texts.map(chars);
		const spread = Math.max(...charCounts) - Math.min(...charCounts);
		if (spread > 4) {
			console.warn(`[quiz] "${label}…" choices differ by ${spread} characters; keep it within 4.`);
		}
	}

	function wire(quiz) {
		const list = quiz.querySelector('.quiz-choices');
		const result = quiz.querySelector('.quiz-result');
		if (!list || !result) return;

		const items = Array.from(list.children);
		const buttons = items
			.map((li) => li.querySelector('button'))
			.filter((b) => b instanceof HTMLButtonElement);
		if (buttons.length < 2) return;

		auditChoices(quiz, buttons);
		shuffle(items).forEach((li) => list.appendChild(li));

		const reset = document.createElement('button');
		reset.type = 'button';
		reset.className = 'quiz-reset';
		reset.hidden = true;
		reset.textContent = 'Try this one again';
		quiz.appendChild(reset);

		const settle = (chosen) => {
			const right = chosen.hasAttribute('data-correct');
			buttons.forEach((b) => {
				b.disabled = true;
				if (b === chosen) {
					b.dataset.mark = right ? 'right' : 'wrong';
				} else if (b.hasAttribute('data-correct')) {
					b.dataset.mark = 'right';
				} else {
					b.dataset.mark = 'dim';
				}
			});

			const verdict = right ? 'Right.' : 'Not this one.';
			const why = chosen.dataset.feedback ?? '';
			const because = right
				? ''
				: (buttons.find((b) => b.hasAttribute('data-correct'))?.dataset.feedback ?? '');
			result.innerHTML = '';
			const strong = document.createElement('b');
			strong.textContent = verdict;
			result.append(strong, ' ', [why, because].filter(Boolean).join(' '));
			reset.hidden = false;
			quiz.dispatchEvent(new CustomEvent('quiz:answered', { bubbles: true, detail: { right } }));
		};

		buttons.forEach((b) => b.addEventListener('click', () => settle(b)));

		reset.addEventListener('click', () => {
			buttons.forEach((b) => {
				b.disabled = false;
				delete b.dataset.mark;
			});
			result.textContent = '';
			reset.hidden = true;
			shuffle(Array.from(list.children)).forEach((li) => list.appendChild(li));
			buttons[0].focus();
		});
	}

	/**
	 * Lesson-wide tally. Counts only the first answer to each question, so
	 * re-trying to reach a better score is not a thing this reports.
	 */
	function wireTally() {
		const tally = document.querySelector('[data-quiz-tally]');
		if (!tally) return;
		const total = document.querySelectorAll('[data-quiz]').length;
		const seen = new WeakSet();
		let asked = 0;
		let right = 0;
		const render = () => {
			tally.textContent = `Recalled ${right} of ${asked} answered — ${total} in this lesson`;
		};
		render();
		document.addEventListener('quiz:answered', (event) => {
			const quiz = event.target;
			if (!(quiz instanceof Element) || seen.has(quiz)) return;
			seen.add(quiz);
			asked += 1;
			if (event.detail?.right) right += 1;
			render();
		});
	}

	const start = () => {
		document.querySelectorAll('[data-quiz]').forEach(wire);
		wireTally();
	};

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start, { once: true });
	} else {
		start();
	}
})();
