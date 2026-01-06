import json
from pathlib import Path
import sys
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from llm.service.openai_client import OpenAIClient
from data.models.llm_ontology_output import ExtractedEventOutput
from data.models.ontology.ontology_description import build_ontology_description


class LLMEventExtractor:
    def __init__(self, openai_client: OpenAIClient):
        self.client = openai_client

    def _build_prompt(self, text: str) -> str:
        ontology = build_ontology_description()

        # Guidance for canonical actor roles to align with the OntologyMapper
        role_guidance = '''
Actor role canonicalization rules (map synonyms to these canonical roles):
- attacker: attacker, perpetrator, assailant
- victim: victim, target, injured
- government: government, state
- organization: organization, company, corp, inc, ltd
- participant: participant, witness, reporter

The `role` field in each actor object must be one of: ["attacker", "victim", "government", "organization", "participant"] or omitted/null if unknown. Use the synonyms above to choose the canonical role.
'''

        return f"""
    You are an assistant that extracts structured event information from unstructured text based on the following ontology:

    {ontology}

    {role_guidance}

    Return ONLY valid JSON matching this schema:

    {ExtractedEventOutput.model_json_schema()}

    Text:
    '''
    {text}
    '''
    """

    def extract_event(
        self,
        text: str,
        source_url: str,
    ) -> ExtractedEventOutput:

        prompt = self._build_prompt(text)

        response = self.client.client.chat.completions.create(
            model=self.client.model,
            messages=[
                {"role": "system", "content": "You extract structured events from unstructured texts."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=2500,
        )

        raw = response.choices[0].message.content

        try:
            data = json.loads(raw)
            data["source_url"] = source_url
            return ExtractedEventOutput(**data)
        except Exception as e:
            raise ValueError(
                f"Invalid LLM output\nRaw:\n{raw}\nError: {e}"
            )
