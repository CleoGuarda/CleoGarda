import { SWAP_TOOLKIT } from "./tools"
import { SWAP_AGENT_ID } from "./name"
import { SWAP_ASSISTANT_GUIDE } from "./description"
import { SWAP_ASSISTANT_SKILLS } from "./capabilities"

import type { AssistantProfile } from "@/ai/agent"

export const swapExecutor: AssistantProfile = {
  id: SWAP_AGENT_ID,
  label: "Swap Executor Agent",
  promptBase: SWAP_ASSISTANT_GUIDE.trim(),
  features: SWAP_ASSISTANT_SKILLS.trim(),
  extensions: SWAP_TOOLKIT,
}
