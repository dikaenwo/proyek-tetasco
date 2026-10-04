export type EggSpecies = 'ayam' | 'puyuh' | 'bebek' | 'angsa' | 'kalkun';
export type IncubationPhase = 'inkubasi' | 'hatching';
export type SystemStatus = 'normal' | 'perlu_perhatian' | 'berbahaya';

export interface IncubationProgram {
  species: EggSpecies;
  nameId: string;
  emoji: string;
  durationDays: number;
  hatchingPhaseStartDay: number;
  targetTemp: number;
  targetTempHatching: number;
  targetHumidity: number;
  targetHumidityHatching: number;
  turningFrequencyHours: number;
  turningAngle: number;
  tempTolerance: number;
  humidityTolerance: number;
  description: string;
  tips: string[];
  color: string;
  bgColor: string;
}

export const IncubationPrograms: Record<EggSpecies, IncubationProgram> = {
  ayam: {
    species: 'ayam', nameId: 'Ayam', emoji: '🐔', durationDays: 21,
    hatchingPhaseStartDay: 18, targetTemp: 37.7, targetTempHatching: 37.2,
    targetHumidity: 60, targetHumidityHatching: 70, turningFrequencyHours: 8,
    turningAngle: 45, tempTolerance: 0.5, humidityTolerance: 5,
    description: 'Program standar untuk telur ayam kampung dan ras',
    tips: ['Putar telur 3x sehari secara rutin', 'Jangan putar telur pada hari 18-21', 'Pastikan ventilasi cukup selama proses menetas'],
    color: '#D98B4A', bgColor: '#FDF0E3',
  },
  puyuh: {
    species: 'puyuh', nameId: 'Puyuh', emoji: '🥚', durationDays: 17,
    hatchingPhaseStartDay: 14, targetTemp: 37.8, targetTempHatching: 37.5,
    targetHumidity: 55, targetHumidityHatching: 75, turningFrequencyHours: 6,
    turningAngle: 45, tempTolerance: 0.3, humidityTolerance: 4,
    description: 'Program untuk telur puyuh yang sensitif terhadap suhu',
    tips: ['Putar lebih sering karena ukuran telur kecil', 'Perhatikan kelembaban terutama pada fase menetas', 'Lakukan candling pada hari ke-7'],
    color: '#8FAF82', bgColor: '#F0F5EE',
  },
  bebek: {
    species: 'bebek', nameId: 'Bebek', emoji: '🦆', durationDays: 28,
    hatchingPhaseStartDay: 25, targetTemp: 37.5, targetTempHatching: 37.0,
    targetHumidity: 65, targetHumidityHatching: 80, turningFrequencyHours: 8,
    turningAngle: 45, tempTolerance: 0.5, humidityTolerance: 5,
    description: 'Program untuk bebek dengan kebutuhan kelembaban tinggi',
    tips: ['Semprot telur dengan air hangat 2x sehari mulai hari ke-7', 'Kelembaban lebih tinggi dari ayam', 'Proses menetas lebih lama, bersabarlah'],
    color: '#4A90D9', bgColor: '#E8F2FD',
  },
  angsa: {
    species: 'angsa', nameId: 'Angsa', emoji: '🦢', durationDays: 30,
    hatchingPhaseStartDay: 27, targetTemp: 37.3, targetTempHatching: 37.0,
    targetHumidity: 65, targetHumidityHatching: 85, turningFrequencyHours: 8,
    turningAngle: 45, tempTolerance: 0.4, humidityTolerance: 5,
    description: 'Program untuk angsa dengan masa inkubasi terpanjang',
    tips: ['Butuh kelembaban sangat tinggi pada fase menetas', 'Putar telur dengan hati-hati karena ukurannya besar', 'Candling pada hari ke-7 dan ke-14'],
    color: '#7B8FA1', bgColor: '#EEF2F5',
  },
  kalkun: {
    species: 'kalkun', nameId: 'Kalkun', emoji: '🦃', durationDays: 28,
    hatchingPhaseStartDay: 25, targetTemp: 37.5, targetTempHatching: 37.0,
    targetHumidity: 60, targetHumidityHatching: 75, turningFrequencyHours: 8,
    turningAngle: 45, tempTolerance: 0.5, humidityTolerance: 5,
    description: 'Program untuk kalkun dengan kebutuhan khusus',
    tips: ['Pastikan suhu sangat stabil', 'Kelembaban relatif sedikit lebih rendah dari bebek', 'Butuh lebih banyak ventilasi'],
    color: '#8A6848', bgColor: '#F5EDE4',
  },
};

export const getIncubationPhase = (day: number, species: EggSpecies): IncubationPhase =>
  day >= IncubationPrograms[species].hatchingPhaseStartDay ? 'hatching' : 'inkubasi';

export const getSystemStatus = (temp: number, humidity: number, species: EggSpecies, phase: IncubationPhase): SystemStatus => {
  const p = IncubationPrograms[species];
  const tTarget = phase === 'hatching' ? p.targetTempHatching : p.targetTemp;
  const hTarget = phase === 'hatching' ? p.targetHumidityHatching : p.targetHumidity;
  const td = Math.abs(temp - tTarget), hd = Math.abs(humidity - hTarget);
  if (td > p.tempTolerance * 2 || hd > p.humidityTolerance * 2) return 'berbahaya';
  if (td > p.tempTolerance || hd > p.humidityTolerance) return 'perlu_perhatian';
  return 'normal';
};

export const getStatusLabel = (s: SystemStatus) =>
  ({ normal: 'Normal', perlu_perhatian: 'Perlu Perhatian', berbahaya: 'Berbahaya' }[s]);
