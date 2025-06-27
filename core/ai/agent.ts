import { Toolset } from "ai"

export type AssistantProfile = {
  label: string
  id: string
  promptBase: string
  features: string
  extensions: Record<string, Toolset>
}

// Alyssium Assistant profile
export const alyssiumAssistant: AssistantProfile = {
  label: "Alyssium Core AI",
  id: "alyssium-core-ai",
  promptBase: `
You are Alyssium Core AI, an engine for deep on-chain analysis on Solana.
Provide clear, structured answers with TypeScript and Python examples,
and offer guidance on integration and optimization of computational models.
  `.trim(),
  features: `
• Token risk score calculation  
• Anomalous transaction detection  
• Model training and risk prediction  
• Data visualization and chart generation  
  `.trim(),
  extensions: {
    logger: {
      name: "EventLogger",
      description: "Logs events and metrics to JSON files",
      run: async ({ params }) => {
        // implementation here
      }
    },
    analytics: {
      name: "DataAnalytics",
      description: "Aggregates and analyzes on-chain metrics",
      run: async ({ params }) => {
        // implementation here
      }
    },
    viz: {
      name: "ChartRenderer",
      description: "Renders charts and graphs in the browser",
      run: async ({ params }) => {
        // implementation here
      }
    }
  }
}
