/**
 * Centralized design tokens for visual consistency across the frontend application.
 */
export const DESIGN_TOKENS = {
  // Animation duration and timing functions
  transitions: {
    duration: {
      fast: 0.15,   // For hover states, tooltips
      normal: 0.25, // For card entrances, page transitions
      slow: 0.4,    // For layout morphing, large collapses
    },
    ease: {
      default: [0.25, 0.1, 0.25, 1], // Standard ease
      subtle: [0.16, 1, 0.3, 1],     // Vercel/Linear style custom ease-out
      spring: { type: "spring", stiffness: 300, damping: 30 },
    }
  },
  
  // Custom border radiuses matching shadcn base theme configurations
  radius: {
    badge: "rounded-md",
    button: "rounded-lg",
    card: "rounded-2xl",
    input: "rounded-xl",
  },

  // Consistent layouts and content width definitions
  layout: {
    maxWidth: "max-w-5xl",
    chatMaxWidth: "max-w-4xl",
    headerHeight: "h-16",
  }
};
