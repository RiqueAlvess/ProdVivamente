'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface FeedbackStepProps {
  onSubmit: (feedback?: string) => void;
  onSkip: () => void;
  isSubmitting: boolean;
}

export function FeedbackStep({ onSubmit, onSkip, isSubmitting }: FeedbackStepProps) {
  const [feedback, setFeedback] = useState('');

  return (
    <Card className="max-w-xl mx-auto">
      <CardHeader>
        <CardTitle>Comentário Final</CardTitle>
        <p className="text-sm text-muted-foreground">
          Opcional: Se desejar, deixe um comentário sobre o ambiente de trabalho ou sugestões de melhoria.
          Seu comentário é completamente anônimo.
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Label htmlFor="feedback">Comentário (opcional)</Label>
          <Textarea
            id="feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Escreva aqui seu comentário ou sugestão..."
            rows={5}
            maxLength={2000}
          />
          <p className="text-xs text-muted-foreground text-right">{feedback.length}/2000</p>
        </div>
      </CardContent>
      <CardFooter className="flex gap-3">
        <Button
          variant="outline"
          className="flex-1"
          onClick={onSkip}
          disabled={isSubmitting}
        >
          Pular e enviar
        </Button>
        <Button
          className="flex-1"
          onClick={() => onSubmit(feedback || undefined)}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Enviando...' : 'Enviar pesquisa'}
        </Button>
      </CardFooter>
    </Card>
  );
}
