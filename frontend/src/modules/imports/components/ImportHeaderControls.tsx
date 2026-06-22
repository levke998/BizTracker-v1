import type { BusinessUnit } from "../../masterData/types/masterData";

type ImportHeaderControlsProps = {
  businessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
};

export function ImportHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
}: ImportHeaderControlsProps) {
  return (
    <div className="business-dashboard-filters topbar-dashboard-filters">
      <label className="field topbar-field">
        <span>Vallalkozas</span>
        <select
          value={selectedBusinessUnitId}
          onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
          className="field-input"
        >
          <option value="">Valassz vallalkozast</option>
          {businessUnits.map((businessUnit) => (
            <option key={businessUnit.id} value={businessUnit.id}>
              {businessUnit.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field">
        <span>Import tipus</span>
        <select value="" disabled onChange={() => undefined} className="field-input">
          <option value="">POS CSV</option>
        </select>
      </label>
    </div>
  );
}
