import React from 'react';
import { Clip } from '../services/api';
import { MultiPlatformPublishModal } from './MultiPlatformPublishModal';

interface YouTubePublishModalProps {
  clip: Clip;
  itemType?: 'clip' | 'meme';
  onClose: () => void;
  onSuccess: () => void;
}

export const YouTubePublishModal: React.FC<YouTubePublishModalProps> = (props) => {
  return <MultiPlatformPublishModal {...props} />;
};
