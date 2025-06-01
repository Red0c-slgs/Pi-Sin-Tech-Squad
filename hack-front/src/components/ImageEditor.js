import React, { useState, useRef, useEffect } from 'react';
import { Stage, Layer, Image, Line, Text, Circle, Transformer } from 'react-konva';
import Button from './ui/Button';
import Input from './ui/Input';
import Dropdown from './ui/Dropdown';

const ImageEditor = ({ imageUrl = 'http://94.154.128.76:9000/user-data/1/8e57a487-8495-4ad5-b663-7ce88a3c19b3.jpg', annotations_from_url=[], setLabelHieght}) => {
  const [image, setImage] = useState(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
  const [annotations, setAnnotations] = useState(annotations_from_url);
  const [selectedAnnotation, setSelectedAnnotation] = useState(null);
  const [selectedClass, setSelectedClass] = useState('пора');
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPoints, setCurrentPoints] = useState([]);
  const [isPanning, setIsPanning] = useState(false);
  const [lastPointerPosition, setLastPointerPosition] = useState(null);
  const [debugInfo, setDebugInfo] = useState('');
  const containerRef = useRef(null);
  const imageRef = useRef(null);
  const stageRef = useRef(null);
  const transformerRef = useRef(null);

  // Define classes with their colors
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

  // Extract just the class names for dropdown and other uses
  const classes = classesConfig.map(c => c.name);

  // Get color for a class name
  const getColorForClass = (className) => {
    const classConfig = classesConfig.find(c => c.name === className);
    return classConfig ? classConfig.color : 'rgb(255, 0, 0)';
  };

  // Get class index by name
  const getClassIndexByName = (className) => {
    const classConfig = classesConfig.find(c => c.name === className);
    return classConfig ? classConfig.id : 0;
  };

  // Load image
  useEffect(() => {
    const img = new window.Image();
    img.crossOrigin = 'Anonymous';
    img.src = imageUrl;
    img.onload = () => {
      setImage(img);
    };
  }, [imageUrl]);

  // Update stage size based on container size
  useEffect(() => {
    if (!containerRef.current) return;

    const updateSize = () => {
      const containerWidth = containerRef.current.offsetWidth;
      const containerHeight = containerRef.current.offsetHeight;
      setStageSize({
        width: containerWidth,
        height: containerHeight
      });
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Convert polygon points to relative coordinates
  const pointsToRelative = (points, imageWidth, imageHeight) => {
    return points.map((point, index) => {
      if (index % 2 === 0) {
        // X coordinate
        return point / imageWidth;
      } else {
        // Y coordinate
        return point / imageHeight;
      }
    });
  };

  // Convert relative coordinates to absolute pixel coordinates
  const relativeToPoints = (relativePoints, imageWidth, imageHeight) => {
    return relativePoints.map((point, index) => {
      if (index % 2 === 0) {
        // X coordinate
        return point * imageWidth;
      } else {
        // Y coordinate
        return point * imageHeight;
      }
    });
  };

  // Calculate centroid of a polygon
  const calculateCentroid = (points) => {
    let sumX = 0;
    let sumY = 0;
    const numPoints = points.length / 2;
    
    for (let i = 0; i < points.length; i += 2) {
      sumX += points[i];
      sumY += points[i + 1];
    }
    
    return {
      x: sumX / numPoints,
      y: sumY / numPoints
    };
  };

  const handleWheel = (e) => {
    e.evt.preventDefault();
    
    const scaleBy = 1.1;
    const stage = e.target.getStage();
    const oldScale = scale;
    const pointerPosition = stage.getPointerPosition();
    
    const mousePointTo = {
      x: (pointerPosition.x - position.x) / oldScale,
      y: (pointerPosition.y - position.y) / oldScale
    };
    
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;
    
    setScale(newScale);
    setPosition({
      x: pointerPosition.x - mousePointTo.x * newScale,
      y: pointerPosition.y - mousePointTo.y * newScale
    });
  };

  const handleMouseDown = (e) => {
    // Check if middle mouse button is pressed (button === 1)
    if (e.evt.button === 1) {
      setIsPanning(true);
      setLastPointerPosition(e.target.getStage().getPointerPosition());
      return;
    }
    
    // Left mouse button for drawing
    if (e.evt.button === 0) {
      const stage = e.target.getStage();
      const pointerPos = stage.getPointerPosition();
      
      // Check if we clicked on the stage background (not on an annotation)
      if (e.target === stage || e.target === imageRef.current) {
        // Start drawing a new polygon
        if (!isDrawing) {
          setIsDrawing(true);
          const adjustedX = (pointerPos.x - position.x) / scale;
          const adjustedY = (pointerPos.y - position.y) / scale;
          setCurrentPoints([adjustedX, adjustedY]);
          
          // Deselect any selected annotation
          setSelectedAnnotation(null);
          
          // Debug info
          setDebugInfo(`Started drawing at ${adjustedX.toFixed(0)}, ${adjustedY.toFixed(0)}`);
        } else {
          // Continue drawing the polygon
          const adjustedX = (pointerPos.x - position.x) / scale;
          const adjustedY = (pointerPos.y - position.y) / scale;
          
          // Add the new point to the current points
          setCurrentPoints([...currentPoints, adjustedX, adjustedY]);
          
          // Debug info
          setDebugInfo(`Added point at ${adjustedX.toFixed(0)}, ${adjustedY.toFixed(0)}`);
        }
      }
    }
  };

  const handleMouseMove = (e) => {
    const stage = e.target.getStage();
    const pointerPos = stage.getPointerPosition();
    
    // Handle panning with middle mouse button
    if (isPanning && lastPointerPosition) {
      const dx = pointerPos.x - lastPointerPosition.x;
      const dy = pointerPos.y - lastPointerPosition.y;
      
      setPosition({
        x: position.x + dx,
        y: position.y + dy
      });
      
      setLastPointerPosition(pointerPos);
      return;
    }
  };

  const handleMouseUp = (e) => {
    // Release middle mouse button
    if (e.evt.button === 1) {
      setIsPanning(false);
      setLastPointerPosition(null);
      return;
    }
  };

  const handleDoubleClick = (e) => {
    // Finish drawing the polygon on double click
    if (isDrawing && currentPoints.length >= 6) { // At least 3 points (6 coordinates)
      if (image) {
        const imageWidth = image.width;
        const imageHeight = image.height;
        
        // Close the polygon by adding the first point again
        let finalPoints = [...currentPoints];
        if (finalPoints[0] !== finalPoints[finalPoints.length - 2] || 
            finalPoints[1] !== finalPoints[finalPoints.length - 1]) {
          finalPoints = [...finalPoints, finalPoints[0], finalPoints[1]];
        }
        
        // Convert to relative coordinates for storage
        const relativePoints = pointsToRelative(finalPoints, imageWidth, imageHeight);
        
        // Add the new annotation
        const newAnnotation = {
          class: selectedClass,
          points: relativePoints
        };
        
        setAnnotations([...annotations, newAnnotation]);
        setLabelHieght([...annotations, newAnnotation])
        
        // Debug info
        setDebugInfo(`Completed polygon with ${finalPoints.length / 2} points`);
      }
      
      // Reset drawing state
      setIsDrawing(false);
      setCurrentPoints([]);
    } else if (isDrawing) {
      // Not enough points, cancel drawing
      setDebugInfo('Cancelled: Need at least 3 points to create a polygon');
      setIsDrawing(false);
      setCurrentPoints([]);
    }
  };

  const handleAnnotationClick = (index) => {
    setSelectedAnnotation(index);
  };

  const handleClassChange = (classValue) => {
    setSelectedClass(classValue);
    
    if (selectedAnnotation !== null) {
      const updatedAnnotations = [...annotations];
      updatedAnnotations[selectedAnnotation].class = classValue;
      setAnnotations(updatedAnnotations);
      setLabelHieght(updatedAnnotations)
    }
  };

  const handleDeleteAnnotation = () => {
    if (selectedAnnotation !== null) {
      const updatedAnnotations = annotations.filter((_, index) => index !== selectedAnnotation);
      setAnnotations(updatedAnnotations);
      setLabelHieght(updatedAnnotations)
      setSelectedAnnotation(null);
    }
  };

  const handleCancelDrawing = () => {
    if (isDrawing) {
      setIsDrawing(false);
      setCurrentPoints([]);
      setDebugInfo('Drawing cancelled');
    }
  };

  const exportAnnotations = () => {
    // Format for export: class_id x1 y1 x2 y2 ... xn yn
    const exportData = annotations.map(ann => {
      const classIndex = getClassIndexByName(ann.class);
      const pointsStr = ann.points.map(p => p.toFixed(6)).join(' ');
      return `${classIndex} ${pointsStr}`;
    }).join('\n');
    
    const blob = new Blob([exportData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'polygon_annotations.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const importAnnotations = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target.result;
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
      
      setAnnotations(newAnnotations);
      setLabelHieght(newAnnotations)
    };
    
    reader.readAsText(file);
  };

  const renderAnnotations = () => {
    if (!image) return null;
    
    const imageWidth = image.width;
    const imageHeight = image.height;
    
    return annotations.map((ann, index) => {
      const absolutePoints = relativeToPoints(ann.points, imageWidth, imageHeight);
      const color = getColorForClass(ann.class);
      const isSelected = selectedAnnotation === index;
      
      return (
        <Line
          key={index}
          points={absolutePoints}
          stroke={isSelected ? 'red' : color}
          strokeWidth={isSelected ? 3 / scale : 2 / scale}
          fill={isSelected ? 'rgba(255, 0, 0, 0.2)' : `${color.replace('rgb', 'rgba').replace(')', ', 0.1)')}` }
          closed={true}
          name={`annotation-${index}`}
          onClick={() => handleAnnotationClick(index)}
          onTap={() => handleAnnotationClick(index)}
          dash={isSelected ? [10 / scale, 5 / scale] : undefined}
        />
      );
    });
  };

  const renderAnnotationLabels = () => {
    if (!image) return null;
    
    const imageWidth = image.width;
    const imageHeight = image.height;
    
    return annotations.map((ann, index) => {
      const absolutePoints = relativeToPoints(ann.points, imageWidth, imageHeight);
      const centroid = calculateCentroid(absolutePoints);
      const isSelected = selectedAnnotation === index;
      
      return (
        <Text
          key={`label-${index}`}
          x={centroid.x}
          y={centroid.y}
          text={ann.class}
          fill="white"
          fontSize={isSelected ? 18 / scale : 16 / scale}
          fontStyle={isSelected ? 'bold' : 'normal'}
          padding={4 / scale}
          background={isSelected ? 'rgba(255, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.7)'}
          align="center"
          verticalAlign="middle"
          offsetX={20}
          offsetY={10}
        />
      );
    });
  };

  const renderCurrentDrawing = () => {
    if (!isDrawing || currentPoints.length < 2) return null;
    
    const color = getColorForClass(selectedClass);
    
    return (
      <>
        <Line
          points={currentPoints}
          stroke={color}
          strokeWidth={2 / scale}
          dash={[5 / scale, 5 / scale]}
          fill={`${color.replace('rgb', 'rgba').replace(')', ', 0.2)')}` }
        />
        {/* Render points as circles */}
        {currentPoints.map((point, index) => {
          if (index % 2 === 0) {
            return (
              <Circle
                key={index / 2}
                x={point}
                y={currentPoints[index + 1]}
                radius={4 / scale}
                fill="white"
                stroke={color}
                strokeWidth={1 / scale}
              />
            );
          }
          return null;
        })}
      </>
    );
  };

  const dropdownOptions = classes.map(cls => ({ label: cls, value: cls }));

  return (
    <div 
      ref={containerRef}
      style={{ 
        display: 'flex', 
        width: '100%', 
        height: 'calc(100vh - 112px)',
        overflow: 'hidden'
      }}
    >
      {/* Image Area (2/3) */}
      <div style={{ 
        width: '66.66%', 
        height: '100%', 
        position: 'relative',
        backgroundColor: '#222',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden'
      }}>
        <Stage
          ref={stageRef}
          width={stageSize.width}
          height={stageSize.height}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onDblClick={handleDoubleClick}
          draggable={false}
          position={position}
          scale={{ x: scale, y: scale }}
        >
          <Layer>
            {image && (
              <Image
                ref={imageRef}
                image={image}
                x={0}
                y={0}
              />
            )}
            {renderAnnotations()}
            {renderAnnotationLabels()}
            {renderCurrentDrawing()}
          </Layer>
        </Stage>
        
        {/* Debug overlay */}
        {debugInfo && (
          <div style={{
            position: 'absolute',
            bottom: 10,
            left: 10,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '5px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'monospace',
            zIndex: 1000
          }}>
            {debugInfo}
          </div>
        )}
        
        {/* Drawing status indicator */}
        {isDrawing && (
          <div style={{
            position: 'absolute',
            top: 10,
            left: 10,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '5px 10px',
            borderRadius: '4px',
            fontSize: '14px',
            fontFamily: 'sans-serif',
            zIndex: 1000
          }}>
            <div>Drawing mode: Click to add points, double-click to finish</div>
            <div>Points: {currentPoints.length / 2}</div>
          </div>
        )}
      </div>

      {/* Control Panel (1/3) */}
      <div style={{ 
        width: '33.33%', 
        height: '100%', 
        padding: '20px',
        overflowY: 'auto',
        backgroundColor: '#f5f5f5',
        borderLeft: '1px solid #ddd',
        color: '#333',
        fontFamily: 'Arial, sans-serif'
      }}>

        <div style={{ marginBottom: '25px' }}>
          <h3 style={{ 
            color: '#2c3e50', 
            fontSize: '18px',
            marginBottom: '10px'
          }}>Annotation Classes</h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: '6px',
            marginBottom: '15px'
          }}>
            {classesConfig.map((cls) => (
              <div 
                key={cls.id}
                onClick={() => setSelectedClass(cls.name)}
                style={{ 
                  backgroundColor: 'var(--primary-color)',
                  color: '#fff',
                  padding: '5px 8px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  textAlign: 'center',
                  border: selectedClass === cls.name ? '2px solid #000' : '2px solid transparent',
                  boxShadow: selectedClass === cls.name ? '0 0 5px rgba(0,0,0,0.5)' : 'none',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontWeight: selectedClass === cls.name ? 'bold' : 'normal',
                  textShadow: '1px 1px 1px rgba(0,0,0,0.5)'
                }}
              >
                {cls.name}
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: '25px' }}>
          <h3 style={{ 
            color: '#2c3e50', 
            fontSize: '18px',
            marginBottom: '10px'
          }}>Drawing Controls</h3>
          
          <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            {isDrawing ? (
              <Button 
                onClick={handleCancelDrawing}
                variant="secondary"
              >
                Cancel Drawing
              </Button>
            ) : (
              <div style={{ 
                backgroundColor: '#e9f7fe', 
                padding: '8px 12px', 
                borderRadius: '4px',
                fontWeight: 'bold',
                width: '100%',
                textAlign: 'center'
              }}>
                Click on image to start drawing
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <Button 
              onClick={handleDeleteAnnotation} 
              disabled={selectedAnnotation === null}
              variant="secondary"
            >
              Delete Selected
            </Button>
            <Button 
              onClick={() => setSelectedAnnotation(null)}
              variant="secondary"
              disabled={selectedAnnotation === null}
            >
              Deselect
            </Button>
          </div>
        </div>

        <div style={{ marginBottom: '25px' }}>
          <h3 style={{ 
            color: '#2c3e50', 
            fontSize: '18px',
            marginBottom: '10px'
          }}>Annotation Data</h3>
          <div style={{ marginBottom: '15px' }}>
            <Button onClick={exportAnnotations}>Export Annotations</Button>
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label 
              htmlFor="import-file" 
              style={{ 
                display: 'block', 
                marginBottom: '8px',
                fontWeight: 'bold',
                color: '#2c3e50'
              }}
            >
              Import Annotations:
            </label>
            <input
              id="import-file"
              type="file"
              accept=".txt"
              onChange={importAnnotations}
              style={{ 
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
          </div>
        </div>

        <div style={{ marginBottom: '25px' }}>
          <h3 style={{ 
            color: '#2c3e50', 
            fontSize: '18px',
            marginBottom: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}>
            <span>Annotation List</span>
            <span style={{ 
              fontSize: '14px', 
              backgroundColor: '#3498db', 
              color: 'white',
              borderRadius: '50%',
              width: '24px',
              height: '24px',
              display: 'inline-flex',
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              {annotations.length}
            </span>
          </h3>
          <div style={{ 
            maxHeight: '200px', 
            overflowY: 'auto',
            border: '1px solid #ddd',
            borderRadius: '4px',
            padding: '10px',
            backgroundColor: 'white',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            {annotations.length === 0 ? (
              <p style={{ color: '#7f8c8d', fontStyle: 'italic', textAlign: 'center' }}>
                No annotations yet. Draw polygons on the image.
              </p>
            ) : (
              <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
                {annotations.map((ann, index) => {
                  const isSelected = selectedAnnotation === index;
                  return (
                    <li 
                      key={index}
                      style={{
                        padding: '8px 10px',
                        margin: '4px 0',
                        backgroundColor: isSelected ? getColorForClass(ann.class).replace('rgb', 'rgba').replace(')', ', 0.3)') : 'transparent',
                        cursor: 'pointer',
                        borderRadius: '4px',
                        border: isSelected ? `2px solid ${getColorForClass(ann.class)}` : '1px solid #ddd',
                        transition: 'all 0.2s ease',
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                      onClick={() => setSelectedAnnotation(index)}
                    >
                      <span style={{ 
                        display: 'inline-block',
                        width: '12px',
                        height: '12px',
                        backgroundColor: getColorForClass(ann.class),
                        marginRight: '8px',
                        borderRadius: '2px'
                      }}></span>
                      <span style={{ 
                        display: 'inline-block', 
                        width: '90px', 
                        fontWeight: isSelected ? 'bold' : 'normal',
                        color: isSelected ? '#000' : '#2c3e50',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {ann.class}
                      </span>
                      <span>
                        {ann.points.length / 2} points
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        <div style={{ 
          backgroundColor: '#f9f9f9', 
          padding: '15px', 
          borderRadius: '8px',
          border: '1px solid #e0e0e0'
        }}>
          <h3 style={{ 
            color: '#2c3e50', 
            fontSize: '18px',
            marginBottom: '10px',
            borderBottom: '1px solid #ddd',
            paddingBottom: '5px'
          }}>Instructions</h3>
          <ul style={{ 
            paddingLeft: '20px',
            color: '#555',
            lineHeight: '1.6'
          }}>
            <li>Select a class from the buttons above</li>
            <li>Click on the image to start drawing a polygon</li>
            <li>Continue clicking to add points to your polygon</li>
            <li>Double-click to complete the polygon</li>
            <li>Click on a polygon to select it</li>
            <li>Use mouse wheel to zoom in/out</li>
            <li>Hold middle mouse button to pan the image</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ImageEditor;
