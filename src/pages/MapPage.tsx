import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import 'leaflet/dist/leaflet.css';
// @ts-ignore
import MarkerClusterGroup from 'react-leaflet-cluster';
import { useQuery } from '@tanstack/react-query';
import { fetchPoints } from '../api/points';
import { fetchResources } from '../api/resources';
import type { DeliveryPoint, Priority } from '../types';
import { getPriorityColor } from '../utils/priorityColors';
import MapSidebar from '../features/MapSidebar';
import CreateOrderModal from '../features/CreateOrderModal';

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

function createColoredIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="width:24px;height:24px;border-radius:50% 50% 50% 0;background:${color};border:2px solid #fff;transform:rotate(-45deg);box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -24],
  });
}

function getPointPriority(_point: DeliveryPoint): Priority {
  return 'normal';
}

const legendItems: { priority: Priority; label: string }[] = [
  { priority: 'normal', label: 'Normal' },
  { priority: 'elevated', label: 'Elevated' },
  { priority: 'critical', label: 'Critical' },
];

export default function MapPage() {
  const [selectedPoint, setSelectedPoint] = useState<DeliveryPoint | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createPointId, setCreatePointId] = useState<number | undefined>();

  const { data: points = [], isLoading, error, refetch } = useQuery({
    queryKey: ['points'],
    queryFn: fetchPoints,
    refetchInterval: 60000,
  });

  const { data: resources = [] } = useQuery({
    queryKey: ['resources'],
    queryFn: fetchResources,
  });

  const handleCreateOrder = (pointId?: number) => {
    setCreatePointId(pointId);
    setShowCreate(true);
    setSelectedPoint(null);
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">Failed to load map data</p>
        <button onClick={() => refetch()} className="bg-blue-600 text-white px-4 py-2 rounded-lg">Retry</button>
      </div>
    );
  }

  return (
    <div className="flex h-full gap-4" style={{ minHeight: 'calc(100vh - 10rem)' }}>
      <div className="flex-1 relative rounded-xl overflow-hidden shadow-sm">
        {isLoading && (
          <div className="absolute inset-0 bg-white/80 z-[1000] flex items-center justify-center">
            <div className="text-gray-500">Loading map...</div>
          </div>
        )}
        <MapContainer
          center={[51.505, -0.09]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MarkerClusterGroup>
            {points.map((point) => (
              <Marker
                key={point.id}
                position={[point.latitude, point.longitude]}
                icon={createColoredIcon(getPriorityColor(getPointPriority(point)))}
                eventHandlers={{ click: () => setSelectedPoint(point) }}
              >
                <Popup>{point.name}</Popup>
              </Marker>
            ))}
          </MarkerClusterGroup>
        </MapContainer>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow p-3 z-[1000]">
          <p className="text-xs font-semibold text-gray-700 mb-2">Priority</p>
          {legendItems.map((item) => (
            <div key={item.priority} className="flex items-center gap-2 text-xs text-gray-600 mb-1">
              <span className="w-3 h-3 rounded-full" style={{ background: getPriorityColor(item.priority) }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>

      {selectedPoint && (
        <MapSidebar
          point={selectedPoint}
          resources={resources}
          onClose={() => setSelectedPoint(null)}
          onCreateOrder={handleCreateOrder}
        />
      )}

      {showCreate && (
        <CreateOrderModal
          isOpen={showCreate}
          onClose={() => setShowCreate(false)}
          initialPointId={createPointId}
        />
      )}
    </div>
  );
}
