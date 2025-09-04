import React from 'react';
import { Server } from '../../types';
import ServerCard from './ServerCard';

interface ServerGalleryProps {
  servers: Server[];
  onServerSelect: (server: Server) => void;
}

const ServerGallery: React.FC<ServerGalleryProps> = ({ servers, onServerSelect }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-6">
      {servers.map((server) => (
        <ServerCard 
          key={server.id}
          server={server}
          onClick={() => onServerSelect(server)}
        />
      ))}
    </div>
  );
};

export default ServerGallery;
