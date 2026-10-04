# Project working rules

Read PROJECT_STATUS.md first. Keep context and output focused on the requested task.
Use one agent unless the user explicitly asks for delegation. Never dump complete catalogue files or tool registries into the conversation.
The current catalogue is data/catalogue-index.json plus data/sets/*.json. Use scripts/catalogue_io.py or scripts/catalogue_io.js; unchanged set files must remain unchanged. data/catalogue.json is a frozen compatibility snapshot only.
Preserve stable card IDs, all legitimate collections and user data. Do not infer checklist numbers or unverified parallels.
Use targeted validation; do not retry known unavailable browser tooling. Report verification gaps honestly and do not claim tests passed unless they ran.
Keep commentary brief and update PROJECT_STATUS.md when work reaches a milestone. Do not deploy unverified UI behaviour without clearly disclosing outstanding checks.
