// MIT No Attribution
//
// Copyright 2025 Amazon Web Services
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * Example component showing how to use the new Spanish translations
 * This is just for demonstration - you can delete this file after reviewing
 */
export function TranslationExample() {
  const { t } = useTranslation();

  return (
    <Card className="max-w-md mx-auto">
      <CardHeader>
        <CardTitle>{t('jobs.title')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Basic translations */}
        <div>
          <h3 className="font-semibold">{t('analysis.newAnalysis')}</h3>
          <p className="text-sm text-gray-600">{t('analysis.createAnalysisDescription')}</p>
        </div>

        {/* Form fields */}
        <div className="space-y-2">
          <label className="text-sm font-medium">{t('analysis.analysisName')} *</label>
          <input 
            placeholder={t('analysis.analysisNamePlaceholder')} 
            className="w-full p-2 border rounded"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">{t('analysis.workload')}</label>
          <input 
            placeholder={t('analysis.workloadPlaceholder')} 
            className="w-full p-2 border rounded"
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <Button>{t('analysis.createAnalysis')}</Button>
          <Button variant="outline">{t('common.cancel')}</Button>
        </div>

        {/* Status messages */}
        <div className="text-sm space-y-1">
          <p className="text-green-600">{t('messages.operationSuccessful')}</p>
          <p className="text-red-600">{t('errors.validationError')}</p>
          <p className="text-blue-600">{t('common.loading')}</p>
        </div>

        {/* Job statuses */}
        <div className="text-sm space-y-1">
          <p>Status: {t('jobs.status.created')}</p>
          <p>Status: {t('jobs.status.analyzing')}</p>
          <p>Status: {t('jobs.status.completed')}</p>
        </div>
      </CardContent>
    </Card>
  );
}
