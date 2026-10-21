/**
 * Validation schemas for itinerary edit forms
 */
import { z } from "zod";

/**
 * Schema for re-plan form validation
 */
export const replanFormSchema = z
  .object({
    trip_duration_days: z
      .number()
      .min(1, "Trip must be at least 1 day")
      .max(14, "Trip cannot exceed 14 days"),

    number_of_travelers: z
      .number()
      .min(1, "At least 1 traveler required")
      .max(20, "Maximum 20 travelers"),

    traveling_with: z.enum(["solo", "partner", "family", "friends"]),

    month_of_travel: z.string().min(1, "Month is required"),

    total_budget: z
      .number()
      .min(1, "Budget must be greater than 0")
      .positive("Budget must be a positive number"),

    budget_currency: z.string().min(2, "Currency is required"),

    travel_styles: z
      .array(z.string())
      .min(1, "Select at least one travel style"),

    dietary_preferences: z.array(z.string()),

    accommodation_tier: z.enum([
      "budget",
      "mid-range",
      "luxury",
      "ultra-luxury",
    ]),

    must_include_places: z.array(z.string()),

    additional_notes: z.string(),

    home_city: z.string().min(1, "Home city is required"),

    home_country: z.string().min(1, "Home country is required"),

    // Optional date fields (for re-plan)
    start_date: z
      .string()
      .nullable()
      .optional()
      .refine(
        (val) => {
          if (!val) return true;
          const date = new Date(val);
          return !isNaN(date.getTime()) && date > new Date();
        },
        { message: "Start date must be in the future" },
      ),

    end_date: z
      .string()
      .nullable()
      .optional()
      .refine(
        (val) => {
          if (!val) return true;
          const date = new Date(val);
          return !isNaN(date.getTime());
        },
        { message: "Invalid end date" },
      ),
  })
  .refine(
    (data) => {
      // If both dates are provided, end must be after start
      if (data.start_date && data.end_date) {
        return new Date(data.end_date) > new Date(data.start_date);
      }
      return true;
    },
    {
      message: "End date must be after start date",
      path: ["end_date"],
    },
  );

export type ReplanFormData = z.infer<typeof replanFormSchema>;

/**
 * Field-level validation helpers
 */
export const fieldValidators = {
  budget: (value: number): string | null => {
    if (value <= 0) return "Budget must be greater than 0";
    if (isNaN(value)) return "Budget must be a valid number";
    return null;
  },

  travelers: (value: number): string | null => {
    if (value < 1) return "At least 1 traveler required";
    if (value > 20) return "Maximum 20 travelers";
    if (!Number.isInteger(value))
      return "Number of travelers must be a whole number";
    return null;
  },

  duration: (value: number): string | null => {
    if (value < 1) return "Trip must be at least 1 day";
    if (value > 14) return "Trip cannot exceed 14 days";
    if (!Number.isInteger(value)) return "Duration must be a whole number";
    return null;
  },

  dateRange: (start: string | null, end: string | null): string | null => {
    if (!start || !end) return null;

    const startDate = new Date(start);
    const endDate = new Date(end);

    if (isNaN(startDate.getTime())) return "Invalid start date";
    if (isNaN(endDate.getTime())) return "Invalid end date";

    if (startDate < new Date()) return "Start date must be in the future";
    if (endDate <= startDate) return "End date must be after start date";

    return null;
  },

  requiredString: (value: string, fieldName: string): string | null => {
    if (!value || value.trim().length === 0) {
      return `${fieldName} is required`;
    }
    return null;
  },

  requiredArray: (value: any[], fieldName: string): string | null => {
    if (!value || value.length === 0) {
      return `Select at least one ${fieldName.toLowerCase()}`;
    }
    return null;
  },
};

/**
 * Calculate diff between two preference objects
 */
export function calculateChangedFields(original: any, updated: any): string[] {
  const changed: string[] = [];

  // Compare all relevant fields
  const fieldsToCompare = [
    "trip_duration_days",
    "number_of_travelers",
    "traveling_with",
    "month_of_travel",
    "total_budget",
    "budget_currency",
    "accommodation_tier",
    "home_city",
    "home_country",
    "additional_notes",
    "start_date",
    "end_date",
  ];

  for (const field of fieldsToCompare) {
    if (original[field] !== updated[field]) {
      changed.push(field);
    }
  }

  // Compare arrays (travel_styles, dietary_preferences, must_include_places)
  const arrayFields = [
    "travel_styles",
    "dietary_preferences",
    "must_include_places",
  ];

  for (const field of arrayFields) {
    const origArray = original[field] || [];
    const updatedArray = updated[field] || [];

    if (
      JSON.stringify([...origArray].sort()) !==
      JSON.stringify([...updatedArray].sort())
    ) {
      changed.push(field);
    }
  }

  return changed;
}

/**
 * Format changed fields for display
 */
export function formatChangedField(
  fieldName: string,
  originalValue: any,
  newValue: any,
): { label: string; before: string; after: string } {
  const formatValue = (val: any): string => {
    if (Array.isArray(val)) return val.join(", ");
    if (typeof val === "number") return val.toString();
    if (typeof val === "boolean") return val ? "Yes" : "No";
    return val?.toString() || "";
  };

  const labels: Record<string, string> = {
    total_budget: "Budget",
    accommodation_tier: "Accommodation Tier",
    number_of_travelers: "Number of Travelers",
    trip_duration_days: "Trip Duration",
    traveling_with: "Traveling With",
    month_of_travel: "Travel Month",
    start_date: "Start Date",
    end_date: "End Date",
    travel_styles: "Travel Styles",
    dietary_preferences: "Dietary Preferences",
    must_include_places: "Bucket List",
    additional_notes: "Special Requests",
    home_city: "Home City",
    home_country: "Home Country",
    budget_currency: "Currency",
  };

  return {
    label: labels[fieldName] || fieldName,
    before: formatValue(originalValue),
    after: formatValue(newValue),
  };
}
