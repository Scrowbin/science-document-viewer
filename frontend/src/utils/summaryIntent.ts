/**
 * Detects chat messages that ask about the whole document ("summarize this document",
 * "what is this paper about"). Such questions match no single passage, so normal Q&A
 * retrieval tends to refuse or answer from one section; the AI panel sends them to the
 * summary endpoint instead. Questions about a specific part ("summarize section 3",
 * "Table 2") or a specific concept ("summarize the attention mechanism") stay normal Q&A.
 *
 * LIMITATION: this is a fixed list of English phrasings. Wordings it does not cover still go
 * through normal Q&A (and may be refused); a few specific questions phrased like summaries
 * may get the whole-document summary instead. Planned replacement: a short routing step in
 * the backend where the local LLM classifies each question as "whole document" or
 * "specific passage" before retrieval (after the Phase 4 evaluation, since rag_service.py
 * must stay unchanged until then).
 */

/** Longest message still considered (longer messages are treated as real questions). */
const MAX_WORDS = 25;
/** A message this short with a summary word ("summary?", "tl;dr please") needs no object. */
const SHORT_WORDS = 4;

/** Lower-case and collapse spaces. */
function plain(text: string): string {
  return text.toLowerCase().replace(/\s+/g, ' ').trim();
}

// ---------------------------------------------------------------- building blocks (on plain text)
const DOC_NOUN = '(?:paper|document|doc|article|pdf|file|study|work|publication|text|manuscript|report|reading)';
/** "this paper", "the pdf", "it" */
const DOC_REF = new RegExp(`\\b(?:(?:this|the|that|your|current)\\s+${DOC_NOUN}|it|this)\\b|\\b${DOC_NOUN}\\b`);

const SUMMARY_WORD = [
  'summari[sz]e', 'summary', 'summaries', 'summarization', 'recap', 'overview', 'synopsis', 'tl;? ?dr',
  'gist', 'sum (?:it |this |that |everything )?up', 'nutshell', 'big picture', 'bottom line', 'rundown',
  'run-down', 'run down', 'high[- ]level', 'eli5', 'key takeaways?', 'takeaways?', 'main points?',
  'key points?', 'highlights?', 'outline', 'abstract of',
].join('|');
const SUMMARY_RE = new RegExp(`(?:^|[^a-z])(?:${SUMMARY_WORD})(?:$|[^a-z])`);

/** Things a paper has as a whole: "main contributions", "key findings". */
const WHOLE_OBJECT = new RegExp(
  '\\b(?:main|key|primary|core|major|central|overall|principal|most important)\\s+' +
    '(?:contributions?|findings?|results?|ideas?|points?|conclusions?|arguments?|messages?|claims?|' +
    'goals?|purposes?|objectives?|topics?|themes?|questions?|insights?|lessons?|novelty|innovations?)\\b',
);

/** Phrasings that always mean "the whole document". */
const WHOLE_DOCUMENT_PHRASES: RegExp[] = [
  // what is it about / what's going on
  new RegExp(`\\bwhat(?:'s| is| are| was)?\\s+(?:${DOC_REF.source})\\s+(?:all\\s+)?about\\b`),
  /\bwhat(?:'s| is)\s+(?:this|it)\s+(?:all\s+)?about\b/,
  new RegExp(`\\bwhat\\s+(?:${DOC_REF.source})\\s+(?:is|was)\\s+(?:all\\s+|really\\s+)?about\\b`),
  new RegExp(`\\bwhat(?:'s| is)\\s+(?:going on|happening|inside|covered|discussed)\\s+in\\s+(?:${DOC_REF.source})`),
  new RegExp(`\\bwhat(?:'s| is)\\s+in\\s+(?:this|the)\\s+${DOC_NOUN}\\b`),
  /^(?:so\s+)?what(?:'s| is)\s+(?:this|it)\s*[?!.]*$/,
  /\bwhat am i (?:reading|looking at)\b/,
  // what does the paper do / say / propose ... (ending the sentence)
  new RegExp(
    `\\bwhat\\s+(?:does|did|do)\\s+(?:${DOC_REF.source})\\s+(?:do|say|cover|discuss|present|propose|describe|` +
      `show|argue|claim|contribute|achieve|talk about|investigate|study|explore|introduce|focus on|deal with)\\s*[?!.]*$`,
  ),
  // explain / describe / tell me about / walk me through + the document
  new RegExp(
    `\\b(?:explain|describe|introduce|review|condense|simplify|break down|go over|go through|walk me through|` +
      `run me through|tell me about|talk me through|brief me on|fill me in on|give me (?:a|an) (?:quick |brief |short )?` +
      `(?:intro|introduction|explanation|description|idea))\\b.*\\b(?:this|the|that)\\s+${DOC_NOUN}\\b`,
  ),
  /\b(?:explain|describe|summari[sz]e|review)\s+(?:it|this)\s*(?:to me|for me|briefly|simply|quickly)?\s*[?!.]*$/,
  new RegExp(`\\b(?:purpose|goal|aim|objective|topic|theme|focus|scope|point|thesis|premise|idea)\\s+of\\s+(?:${DOC_REF.source})\\s*[?!.]*$`),
  new RegExp(`\\bwhy\\s+(?:was|is)\\s+(?:this|the)\\s+${DOC_NOUN}\\s+(?:written|important)\\b`),
];

/** References to one part of the document: keep these as normal Q&A. */
const SPECIFIC_PART = new RegExp(
  '\\b(?:section|subsection|chapter|table|figure|fig\\.?|page|paragraph|appendix|equation|eq\\.?|algorithm|line|footnote)\\s*\\d' +
    '|\\b(?:this|that|the following|the above|first|second|third|last|next|previous)\\s+' +
    '(?:section|subsection|chapter|table|figure|page|paragraph|appendix|equation|algorithm|sentence|part)\\b' +
    '|\\b(?:introduction|related work|methodology section|results section|conclusion section|abstract section)\\b',
  'i',
);

/** "summarize the attention mechanism": a summary word aimed at something other than the document. */
const NAMED_OTHER_OBJECT = /\b(?:summari[sz]e|recap|overview of|outline)\s+(?:the\s+|a\s+|an\s+)?([a-z0-9-]+(?:\s+[a-z0-9-]+){0,3})/;

function aimsAtSomethingElse(p: string): boolean {
  const m = NAMED_OTHER_OBJECT.exec(p);
  if (!m) return false;
  const object = m[1];
  // aimed at the document itself, a pronoun, or a whole-document object -> not "something else"
  if (new RegExp(`^(?:this|it|that|everything|${DOC_NOUN})\\b`).test(object)) return false;
  if (WHOLE_OBJECT.test(`main ${object}`) || WHOLE_OBJECT.test(object)) return false;
  if (/^(?:please|for me|briefly|quickly|in |again|pls|plz|thanks?)\b/.test(object)) return false;
  return true;
}

export function isWholeDocumentRequest(message: string): boolean {
  const p = plain(message);
  if (!p) return false;
  const words = p.split(' ').length;
  if (words > MAX_WORDS) return false;
  if (SPECIFIC_PART.test(p)) return false;

  if (WHOLE_DOCUMENT_PHRASES.some((re) => re.test(p))) return true;

  if (SUMMARY_RE.test(p)) {
    if (aimsAtSomethingElse(p)) return false;
    if (words <= SHORT_WORDS || DOC_REF.test(p) || WHOLE_OBJECT.test(p)) return true;
    // "can you give me a quick overview please" -> only filler words around the summary word
    const rest = p
      .replace(SUMMARY_RE, ' ')
      .replace(/\b(?:can|could|would|will|you|please|pls|plz|give|me|us|a|an|quick|brief|short|small|tiny|simple|fast|of|i|want|need|like|to|get|provide|write|make|do|just|the|some|hey|hi|ok|okay|now|for)\b/g, ' ')
      .replace(/[^a-z]/g, '');
    return rest.length === 0;
  }

  // "What are the key findings?"
  if (WHOLE_OBJECT.test(p) && (words <= 8 || DOC_REF.test(p))) return true;
  return false;
}
