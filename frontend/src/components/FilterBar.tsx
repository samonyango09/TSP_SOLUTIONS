import type { OutletFacets, OutletType } from "../api/types";
import { OUTLET_TYPE_LABEL } from "../lib/display";

interface FilterBarProps {
  facets: OutletFacets | null;
  type: OutletType | "";
  county: string;
  onTypeChange: (type: OutletType | "") => void;
  onCountyChange: (county: string) => void;
}

export default function FilterBar({ facets, type, county, onTypeChange, onCountyChange }: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <select
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        value={type}
        onChange={(e) => onTypeChange(e.target.value as OutletType | "")}
      >
        <option value="">All outlet types</option>
        {facets?.types.map((t) => (
          <option key={t} value={t}>
            {OUTLET_TYPE_LABEL[t]}
          </option>
        ))}
      </select>
      <select
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        value={county}
        onChange={(e) => onCountyChange(e.target.value)}
      >
        <option value="">All counties</option>
        {facets?.counties.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </div>
  );
}
