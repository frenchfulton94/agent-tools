/* =============================================================================
   router-drill.js — interleaved routing practice. Many prompts, one fixed set
   of schema buttons, immediate feedback naming the rule that decided it.
   -----------------------------------------------------------------------------
   MARKUP CONTRACT

     <div class="drill" data-drill
          data-choices="hotfix,setup,bugfix,upgrade,refactor,spike,feature,rapid">
       <p class="drill-score" data-drill-score></p>
       <ol class="drill-items">
         <li data-answer="bugfix" data-rule="3"
             data-why="Behaves wrong versus intent, and performance work routes here too.">
           "The CSV export is dropping the last row for accounts in Alaska."
         </li>
       </ol>
       <noscript><p class="drill-noscript">…answers, for reading without JS…</p></noscript>
     </div>

   Item order is shuffled on load: interleaving is the point. A learner who
   works the list in written order learns the order, not the routing rule.

   The choice buttons stay in the authored order for every item, because the
   real decision tree is ordered and first match wins — the learner should be
   scanning the same sequence each time, which is the skill being trained.
   ========================================================================== */

(() => {
	'use strict';

	function shuffle(list) {
		for (let i = list.length - 1; i > 0; i -= 1) {
			const j = Math.floor(Math.random() * (i + 1));
			[list[i], list[j]] = [list[j], list[i]];
		}
		return list;
	}

	function wire(drill) {
		const choices = (drill.dataset.choices ?? '')
			.split(',')
			.map((s) => s.trim())
			.filter(Boolean);
		const list = drill.querySelector('.drill-items');
		const score = drill.querySelector('[data-drill-score]');
		if (!list || choices.length < 2) return;

		const items = Array.from(list.children).filter((li) => li.dataset.answer);
		if (items.length === 0) return;

		let answered = 0;
		let right = 0;
		const render = () => {
			if (!score) return;
			score.textContent =
				answered === 0
					? `${items.length} prompts — route each one`
					: `${right} of ${answered} routed correctly · ${items.length - answered} left`;
		};

		items.forEach((li) => {
			const prompt = document.createElement('p');
			prompt.className = 'drill-prompt';
			prompt.textContent = li.textContent.trim();
			li.textContent = '';
			li.appendChild(prompt);

			const row = document.createElement('ul');
			row.className = 'drill-choices';
			const buttons = choices.map((name) => {
				const cell = document.createElement('li');
				const button = document.createElement('button');
				button.type = 'button';
				button.textContent = name;
				cell.appendChild(button);
				row.appendChild(cell);
				return button;
			});
			li.appendChild(row);

			const result = document.createElement('p');
			result.className = 'drill-result';
			result.setAttribute('role', 'status');
			result.setAttribute('aria-live', 'polite');
			li.appendChild(result);

			buttons.forEach((button) => {
				button.addEventListener('click', () => {
					const picked = button.textContent ?? '';
					const correct = li.dataset.answer ?? '';
					const ok = picked === correct;

					buttons.forEach((b) => {
						b.disabled = true;
						const label = b.textContent ?? '';
						if (label === correct) b.dataset.mark = 'right';
						else if (b === button) b.dataset.mark = 'wrong';
						else b.dataset.mark = 'dim';
					});

					const rule = li.dataset.rule ? `Rule ${li.dataset.rule}. ` : '';
					result.innerHTML = '';
					const verdict = document.createElement('b');
					verdict.textContent = ok ? `${correct}. Right.` : `${correct}, not ${picked}.`;
					result.append(verdict, ' ', rule + (li.dataset.why ?? ''));

					answered += 1;
					if (ok) right += 1;
					render();
				});
			});
		});

		shuffle(items).forEach((li) => list.appendChild(li));
		render();

		const noscript = drill.querySelector('noscript');
		if (noscript) noscript.remove();
	}

	const start = () => document.querySelectorAll('[data-drill]').forEach(wire);

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start, { once: true });
	} else {
		start();
	}
})();
