import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from "react-leaflet";

export interface MapPoint {
  id: string;
  lat: number;
  lon: number;
  color: string;
  label: string;
}

interface MapViewProps {
  points: MapPoint[];
  routeLine?: [number, number][];
  height?: string;
}

const KENYA_CENTER: [number, number] = [-1.2921, 36.8219];

function computeCenter(points: MapPoint[], routeLine?: [number, number][]): [number, number] {
  if (routeLine && routeLine.length > 0) {
    const midIdx = Math.floor(routeLine.length / 2);
    return routeLine[midIdx];
  }
  if (points.length > 0) {
    const lat = points.reduce((sum, p) => sum + p.lat, 0) / points.length;
    const lon = points.reduce((sum, p) => sum + p.lon, 0) / points.length;
    return [lat, lon];
  }
  return KENYA_CENTER;
}

// No default Leaflet Marker icon here on purpose - its default image paths
// don't resolve correctly through Vite's bundling, and CircleMarker (plain
// SVG, color-coded per outlet/customer type) sidesteps that entirely while
// also making type/status easier to distinguish at a glance than a pin would.
export default function MapView({ points, routeLine, height = "500px" }: MapViewProps) {
  const center = computeCenter(points, routeLine);
  const zoom = routeLine && routeLine.length > 0 ? 8 : points.length > 0 ? 10 : 6;

  return (
    <div style={{ height }} className="overflow-hidden rounded-lg border border-slate-200">
      <MapContainer center={center} zoom={zoom} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {routeLine && routeLine.length > 1 && <Polyline positions={routeLine} pathOptions={{ color: "#2563eb", weight: 4 }} />}
        {points.map((p) => (
          <CircleMarker key={p.id} center={[p.lat, p.lon]} radius={7} pathOptions={{ color: p.color, fillColor: p.color, fillOpacity: 0.8 }}>
            <Popup>{p.label}</Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
