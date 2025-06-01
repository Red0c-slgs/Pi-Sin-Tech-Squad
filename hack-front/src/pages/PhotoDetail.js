import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { PhotoProvider, PhotoView } from 'react-photo-view';
// import 'react-photo-view/build/react-photo-view.css'; // Стили для галереи [[3]]
import ImageEditor from '../components/ImageEditor';

const PROXY_URL = process.env.REACT_APP_PROXY_URL || '';

const classesConfig = [
    { id: 0, name: 'пора', color: 'rgb(255, 50, 50)' },
    { id: 1, name: 'включение', color: 'rgb(0, 255, 0)' },
    { id: 2, name: 'подрез', color: 'rgb(0, 0, 255)' },
    { id: 3, name: 'прожог', color: 'rgb(255, 255, 0)' },
    { id: 4, name: 'трещина', color: 'rgb(255, 0, 255)' },
    { id: 5, name: 'наплыв', color: 'rgb(0, 255, 255)' },
    { id: 6, name: 'эталон1', color: 'rgb(255, 64, 64)' },
    { id: 7, name: 'эталон2', color: 'rgb(64, 255, 64)' },
    { id: 8, name: 'эталон3', color: 'rgb(0, 0, 128)' },
    { id: 9, name: 'пора-скрытая', color: 'rgb(128, 128, 0)' },
    { id: 10, name: 'утяжина', color: 'rgb(128, 0, 128)' },
    { id: 11, name: 'несплавление', color: 'rgb(0, 128, 128)' },
    { id: 12, name: 'непровар корня', color: 'rgb(192, 192, 192)' }
  ];

// Основной компонент страницы
const PhotoDetail = () => {
  const { projectId, photoId } = useParams();
  const [imageData, setImageData] = useState(null);
  const [yoloData, setYoloData] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [yoloLabel, setYoloLabel] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${PROXY_URL}/projects/${projectId}/files/${photoId}`);
        if (!response.ok) throw new Error('Ошибка загрузки данных');
        const data = await response.json();
        setImageData(data);
        
        // Если есть разметка YOLO, загружаем её
        if (data.s3_txt_url) {
          const yoloResponse = await fetch(data.s3_txt_url);
          const yoloText = await yoloResponse.text();
          setYoloData(yoloText);
        } 
        setYoloLabel(const_text_to_annatetion(data.label))
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId, photoId]);

  const const_text_to_annatetion = (content) => {
      const lines = content.split('\n').filter(line => line.trim() !== '');
      
      const newAnnotations = lines.map(line => {
        const parts = line.trim().split(' ');
        const classIndex = parseInt(parts[0], 10);
        const className = classesConfig.find(c => c.id === classIndex)?.name || 'unknown';
        
        // Extract points (all values after the class index)
        const points = parts.slice(1).map(parseFloat);
        
        return {
          class: className,
          points: points
        };
      });
      return newAnnotations;
  } 

const handleDelete = async () => {
  if (window.confirm('Are you sure you want to delete this file?')) {
    try {
      const response = await fetch(`${PROXY_URL}/projects/${projectId}/files/${photoId}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (response.ok) {
        console.log('File deleted successfully');
      } else {
        console.error('Failed to delete file');
      }
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  }
};

const handleVerify = async () => {
  try {
    const response = await fetch(`${PROXY_URL}/projects/${projectId}/files/${photoId}`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      body: '',
    });

    if (response.ok) {
      console.log('File verified successfully');
    } else {
      console.error('Failed to verify file');
    }
  } catch (error) {
    console.error('Error verifying file:', error);
  }
};

  const getClassIndexByName = (className) => {
    const classConfig = classesConfig.find(c => c.name === className);
    return classConfig ? classConfig.id : 0;
  };


const handleSave = async () => {
  try {
    const exportData = yoloLabel.map(ann => {
      const classIndex = getClassIndexByName(ann.class);
      const pointsStr = ann.points.map(p => p.toFixed(6)).join(' ');
      return `${classIndex} ${pointsStr}`;
    }).join('\n');
    const response = await fetch(`${PROXY_URL}/yolo?project_id=${projectId}&file_id=${photoId}&label=${encodeURIComponent(exportData)}`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      body: '', // как в curl
    });

    if (response.ok) {
      console.log('Changes saved successfully');
    } else {
      console.error('Failed to save changes');
    }
  } catch (error) {
    console.error('Error saving changes:', error);
  }
};

const get_report = async () =>{
    try {
      const response = await fetch(`${PROXY_URL}/projects/${projectId}/files/${photoId}/report`, {
        method: 'GET'
      });

    if (!response.ok) {
          throw new Error('Failed to fetch the file');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Укажите имя файла, которое хотите сохранить
        a.download = 'report.pdf'; // или получите имя из response.headers
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        console.log('File downloaded successfully');

  } catch (error) {
    console.error('Error verifying file:', error);
  }
}

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error}</div>;

  return (
    <div style={{ height: 'calc(100vh - 64px)', width: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* File info and action panel */}
      <div style={{ 
        padding: '10px 16px', 
        backgroundColor: 'var(--primary-color)', 
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontWeight: 'medium' }}>
          {imageData?.filename || 'Untitled Image'}
        </div>
        <div>
          <button 
            onClick={get_report}
            style={{ 
              marginRight: '8px', 
              padding: '6px 12px', 
              backgroundColor: 'rgb(157 157 44)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            получить отчёт
          </button>
          <button 
            onClick={handleDelete}
            style={{ 
              marginRight: '8px', 
              padding: '6px 12px', 
              backgroundColor: '#f44336', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Удалить
          </button>
          <button 
            onClick={handleVerify}
            style={{ 
              marginRight: '8px', 
              padding: '6px 12px', 
              backgroundColor: '#2196f3', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Разметить
          </button>
          <button 
            onClick={handleSave}
            style={{ 
              padding: '6px 12px', 
              backgroundColor: '#4caf50', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Сохранить разметку
          </button>
        </div>
      </div>

      {/* Image Editor */}
      <div style={{ flex: 1 }}>
        {imageData && (
          <ImageEditor imageUrl={imageData.s3_url || 'http://94.154.128.76:9000/user-data/1/8e57a487-8495-4ad5-b663-7ce88a3c19b3.jpg'} annotations_from_url={yoloLabel} setLabelHieght={setYoloLabel} />
        )}
        {!imageData && (
          <ImageEditor />
        )}
      </div>
    </div>
  );
};

export default PhotoDetail;
