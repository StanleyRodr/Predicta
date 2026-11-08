import { CONCEPTS, type ConceptKey } from "../../lib/conceptExplanations";
import { InfoHint } from "../ui";

/** The info button of one forecast concept, with its plain-language explanation. */
export function ConceptHint({ concept }: { concept: ConceptKey }) {
  const { title, explanation } = CONCEPTS[concept];
  return <InfoHint label={title}>{explanation}</InfoHint>;
}
