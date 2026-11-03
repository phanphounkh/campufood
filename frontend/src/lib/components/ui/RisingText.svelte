<!--
	Reveals text one letter at a time, left to right, each letter rising into place.
	The letters are aria-hidden: give the parent an aria-label (or other accessible name)
	carrying the same text. The animation replays whenever `text` changes (e.g. language switch).
-->
<script lang="ts">
	let {
		text,
		delay = 0,
		stagger = 35,
		class: className = ''
	}: {
		text: string;
		/** ms before the first letter starts */
		delay?: number;
		/** ms between consecutive letters */
		stagger?: number;
		class?: string;
	} = $props();

	/** Khmer subscript sign: it fuses with the following consonant into one glyph. */
	const COENG = '្';

	type Part = { space: true; text: string } | { space: false; letters: string[]; start: number };

	function segment(value: string, granularity: 'word' | 'grapheme'): string[] {
		if (typeof Intl !== 'undefined' && 'Segmenter' in Intl) {
			const segmenter = new Intl.Segmenter(undefined, { granularity });
			return Array.from(segmenter.segment(value), (s) => s.segment);
		}
		return granularity === 'word' ? value.split(/(\s+)/).filter(Boolean) : Array.from(value);
	}

	/** Grapheme clusters, keeping Khmer consonant stacks (ក + ្ + ក) together so they still shape. */
	function letters(word: string): string[] {
		const out: string[] = [];
		for (const g of segment(word, 'grapheme')) {
			if (out.length > 0 && out[out.length - 1].endsWith(COENG)) out[out.length - 1] += g;
			else out.push(g);
		}
		return out;
	}

	const parts = $derived.by(() => {
		let index = 0;
		return segment(text, 'word').map((seg): Part => {
			if (/^\s+$/.test(seg)) return { space: true, text: seg };
			const part: Part = { space: false, letters: letters(seg), start: index };
			index += part.letters.length;
			return part;
		});
	});
</script>

{#key text}
	<!-- Words are kept unbreakable; <wbr> marks word boundaries in scripts without spaces (Khmer). -->
	<span class={className} aria-hidden="true"
		>{#each parts as part, p (p)}{#if part.space}{part.text}{:else}{#if p > 0 && !parts[p - 1].space}<wbr
					/>{/if}<span class="whitespace-nowrap"
					>{#each part.letters as letter, i (i)}<span
							class="letter"
							style:animation-delay="{delay + (part.start + i) * stagger}ms">{letter}</span
						>{/each}</span
				>{/if}{/each}</span
	>
{/key}

<style>
	.letter {
		display: inline-block;
		animation: letter-rise 650ms cubic-bezier(0.34, 1.4, 0.64, 1) both;
	}

	@keyframes letter-rise {
		from {
			opacity: 0;
			transform: translateY(0.65em);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.letter {
			animation: none;
		}
	}
</style>
