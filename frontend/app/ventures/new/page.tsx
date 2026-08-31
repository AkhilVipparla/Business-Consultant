"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { createVenture } from "@/lib/api";

interface FormState {
  title: string;
  one_liner: string;
  description: string;
  target_market: string;
  industry: string;
}

// Mirrors anchor.md/DATABASE_SCHEMA.md's VALIDATION RULES table — keep in
// sync if that table changes.
interface FormErrors {
  title?: string;
  one_liner?: string;
  description?: string;
}

const initialForm: FormState = {
  title: "",
  one_liner: "",
  description: "",
  target_market: "",
  industry: "",
};

function validate(form: FormState): FormErrors {
  const errors: FormErrors = {};
  if (!form.title.trim()) {
    errors.title = "Title is required.";
  } else if (form.title.length > 200) {
    errors.title = "Title must be under 200 characters.";
  }
  if (!form.one_liner.trim()) {
    errors.one_liner = "A one-line description is required.";
  }
  if (!form.description.trim()) {
    errors.description = "A description is required.";
  }
  return errors;
}

export default function NewVenturePage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(initialForm);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const validationErrors = validate(form);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setSubmitting(true);
    setSubmitError(null);
    try {
      const venture = await createVenture({
        title: form.title.trim(),
        one_liner: form.one_liner.trim(),
        description: form.description.trim(),
        target_market: form.target_market.trim() || undefined,
        industry: form.industry.trim() || undefined,
      });
      // The live pipeline view (app/ventures/[id]/page.tsx) auto-starts
      // validation via SSE as soon as it mounts.
      router.push(`/ventures/${venture.id}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Something went wrong. Please try again.",
      );
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="font-heading text-3xl font-bold text-charcoal">New Venture</h1>
      <p className="mt-2 text-muted">
        Describe your idea and VentureMind AI will validate it against real market, competitor,
        and customer research.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5" noValidate>
        <FormField
          id="title"
          label="Title"
          value={form.title}
          onChange={(v) => updateField("title", v)}
          error={errors.title}
          maxLength={200}
          required
        />
        <FormField
          id="one_liner"
          label="One-line description"
          value={form.one_liner}
          onChange={(v) => updateField("one_liner", v)}
          error={errors.one_liner}
          required
        />
        <FormField
          id="description"
          label="Description"
          value={form.description}
          onChange={(v) => updateField("description", v)}
          error={errors.description}
          required
          textarea
        />
        <FormField
          id="target_market"
          label="Target market"
          value={form.target_market}
          onChange={(v) => updateField("target_market", v)}
          helperText="Optional"
        />
        <FormField
          id="industry"
          label="Industry"
          value={form.industry}
          onChange={(v) => updateField("industry", v)}
          helperText="Optional"
        />

        {submitError ? (
          <p role="alert" className="text-sm text-error">
            {submitError}
          </p>
        ) : null}

        <Button type="submit" disabled={submitting}>
          {submitting ? "Submitting..." : "Validate this idea"}
        </Button>
      </form>
    </main>
  );
}

interface FormFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  helperText?: string;
  required?: boolean;
  maxLength?: number;
  textarea?: boolean;
}

// Follows anchor.md/UI_UX_GUIDELINES.md's Form Layout / Input Fields specs.
function FormField({
  id,
  label,
  value,
  onChange,
  error,
  helperText,
  required,
  maxLength,
  textarea,
}: FormFieldProps) {
  const fieldClassName = `w-full rounded-sm bg-surface px-3.5 py-2.5 text-base text-charcoal outline-none transition-colors focus:border-2 focus:border-terracotta ${
    error ? "border-2 border-error" : "border border-border"
  }`;
  const errorId = `${id}-error`;

  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-charcoal">
        {label}
        {required ? <span className="text-error"> *</span> : null}
      </label>
      {textarea ? (
        <textarea
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          className={fieldClassName}
          aria-required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
        />
      ) : (
        <input
          id={id}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          maxLength={maxLength}
          className={fieldClassName}
          aria-required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
        />
      )}
      {error ? (
        <p id={errorId} className="mt-1 text-sm text-error">
          {error}
        </p>
      ) : helperText ? (
        <p className="mt-1 text-sm text-muted">{helperText}</p>
      ) : null}
    </div>
  );
}
