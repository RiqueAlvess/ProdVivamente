'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { Demographics } from '@/types';

interface DemographicsStepProps {
  onNext: (demographics: Demographics) => void;
  onSkip: () => void;
}

export function DemographicsStep({ onNext, onSkip }: DemographicsStepProps) {
  const [gender, setGender] = useState<Demographics['gender']>();
  const [ageRange, setAgeRange] = useState<Demographics['age_range']>();
  const [timeAtCompany, setTimeAtCompany] = useState<Demographics['time_at_company']>();

  function handleNext() {
    onNext({ gender, age_range: ageRange, time_at_company: timeAtCompany });
  }

  return (
    <Card className="max-w-xl mx-auto">
      <CardHeader>
        <CardTitle>Dados Demográficos</CardTitle>
        <p className="text-sm text-muted-foreground">
          Estas informações são opcionais e completamente anônimas. Ajudam-nos a entender melhor o contexto.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label>Gênero</Label>
          <Select onValueChange={(v) => setGender(v as Demographics['gender'])}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione (opcional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="M">Masculino</SelectItem>
              <SelectItem value="F">Feminino</SelectItem>
              <SelectItem value="NB">Não binário</SelectItem>
              <SelectItem value="NO_ANSWER">Prefiro não informar</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Faixa etária</Label>
          <Select onValueChange={(v) => setAgeRange(v as Demographics['age_range'])}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione (opcional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="18-24">18–24 anos</SelectItem>
              <SelectItem value="25-34">25–34 anos</SelectItem>
              <SelectItem value="35-44">35–44 anos</SelectItem>
              <SelectItem value="45-54">45–54 anos</SelectItem>
              <SelectItem value="55+">55+ anos</SelectItem>
              <SelectItem value="NO_ANSWER">Prefiro não informar</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Tempo na empresa</Label>
          <Select onValueChange={(v) => setTimeAtCompany(v as Demographics['time_at_company'])}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione (opcional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="<1">Menos de 1 ano</SelectItem>
              <SelectItem value="1-3">1–3 anos</SelectItem>
              <SelectItem value="3-5">3–5 anos</SelectItem>
              <SelectItem value="5-10">5–10 anos</SelectItem>
              <SelectItem value="10+">Mais de 10 anos</SelectItem>
              <SelectItem value="NO_ANSWER">Prefiro não informar</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
      <CardFooter className="flex gap-3">
        <Button variant="outline" className="flex-1" onClick={onSkip}>
          Pular esta etapa
        </Button>
        <Button className="flex-1" onClick={handleNext}>
          Continuar
        </Button>
      </CardFooter>
    </Card>
  );
}
