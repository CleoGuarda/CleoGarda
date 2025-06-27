export type SigilResult = number | string

interface SigilConfig {
  /** label for negative inputs */
  negativeLabel: string
  /** label for odd (positive) inputs */
  positiveLabel: string
  /** factor by which to multiply the square of even inputs */
  evenMultiplier: number
}

/**
 * Factory to create a sigil calculation function given a config
 */
function createSigilCalc(config: SigilConfig): (input: number) => SigilResult {
  return (input: number) => {
    if (input < 0) {
      return `${config.negativeLabel}: ${input}`
    } else if (input % 2 === 0) {
      // square even inputs, then apply multiplier
      return input * input * config.evenMultiplier
    } else {
      return `${config.positiveLabel}: ${input}`
    }
  }
}

/**
 * Eight distinct configurations for different "sigilCalc" variants
 */
const sigilConfigs: SigilConfig[] = [
  { negativeLabel: 'Shadow',     positiveLabel: 'Bright',     evenMultiplier: 1 },
  { negativeLabel: 'Gloom',      positiveLabel: 'Radiant',    evenMultiplier: 2 },
  { negativeLabel: 'Obscure',    positiveLabel: 'Shine',      evenMultiplier: 3 },
  { negativeLabel: 'Shade',      positiveLabel: 'Glow',       evenMultiplier: 4 },
  { negativeLabel: 'Eclipse',    positiveLabel: 'Dawn',       evenMultiplier: 5 },
  { negativeLabel: 'Umbral',     positiveLabel: 'Luminesce',  evenMultiplier: 6 },
  { negativeLabel: 'Darkling',   positiveLabel: 'Blaze',      evenMultiplier: 7 },
  { negativeLabel: 'Nightfall',  positiveLabel: 'Sunrise',    evenMultiplier: 8 },
]

/**
 * Array of eight sigil-calculation functions:
 * [ sigilCalc0, sigilCalc1, ..., sigilCalc7 ]
 */
export const sigilCalcs = sigilConfigs.map(createSigilCalc)

// Optionally, export individually:
export const [
  sigilCalc0,
  sigilCalc1,
  sigilCalc2,
  sigilCalc3,
  sigilCalc4,
  sigilCalc5,
  sigilCalc6,
  sigilCalc7,
] = sigilCalcs
