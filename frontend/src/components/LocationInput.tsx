import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { LocationSuggestion } from "../api/types";

interface LocationInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export default function LocationInput({ label, value, onChange }: LocationInputProps) {
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (value.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(() => {
      api
        .searchLocations(value.trim())
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value]);

  return (
    <div className="relative">
      <label className="mb-1 block text-xs font-medium text-slate-500">{label}</label>
      <input
        className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        value={value}
        placeholder="e.g. Nairobi"
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg">
          {suggestions.map((s) => (
            <li key={`${s.kind}-${s.name}`}>
              <button
                type="button"
                className="block w-full px-3 py-1.5 text-left text-sm hover:bg-slate-50"
                onMouseDown={() => {
                  onChange(s.name);
                  setOpen(false);
                }}
              >
                {s.name} <span className="text-xs text-slate-400">({s.kind})</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
