'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { SurveyQuestion } from '@/types';

const SCALE_OPTIONS = [
  { value: 0, label: 'Nunca' },
  { value: 1, label: 'Raramente' },
  { value: 2, label: 'Às vezes' },
  { value: 3, label: 'Frequentemente' },
  { value: 4, label: 'Sempre' },
] as const;

interface QuestionStepProps {
  question: SurveyQuestion;
  currentIndex: number;
  totalQuestions: number;
  selectedValue: number | undefined;
  onSelect: (value: number) => void;
  onNext: () => void;
  onPrevious: () => void;
}

export function QuestionStep({
  question,
  currentIndex,
  totalQuestions,
  selectedValue,
  onSelect,
  onNext,
  onPrevious,
}: QuestionStepProps) {
  const progress = ((currentIndex + 1) / totalQuestions) * 100;

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">
            Pergunta {currentIndex + 1} de {totalQuestions}
          </span>
          <span className="text-sm font-medium text-muted-foreground">{question.dimension}</span>
        </div>
        <Progress value={progress} className="h-2" />
        <CardTitle className="text-lg mt-4 leading-relaxed">{question.text}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-2">
          {SCALE_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => onSelect(option.value)}
              className={cn(
                'flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all text-sm font-medium',
                selectedValue === option.value
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border hover:border-primary/50 hover:bg-primary/5'
              )}
            >
              <span className="text-2xl font-bold">{option.value}</span>
              <span className="text-xs text-center leading-tight">{option.label}</span>
            </button>
          ))}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between gap-3">
        <Button
          variant="outline"
          onClick={onPrevious}
          disabled={currentIndex === 0}
        >
          Anterior
        </Button>
        <Button
          onClick={onNext}
          disabled={selectedValue === undefined}
        >
          {currentIndex === totalQuestions - 1 ? 'Finalizar perguntas' : 'Próxima'}
        </Button>
      </CardFooter>
    </Card>
  );
}
