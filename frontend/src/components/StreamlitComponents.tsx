'use client';

import React, { useState } from 'react';
import { Info, CheckCircle2, AlertTriangle, XCircle, ChevronDown, ChevronRight, X } from 'lucide-react';

// =========================================================
// Streamlit Metric Card
// =========================================================
export const StMetric: React.FC<{ label: string; value: string | number }> = ({ label, value }) => {
  return (
    <div className="st-metric-card flex-1 min-w-[140px]">
      <div className="st-metric-label">{label}</div>
      <div className="st-metric-value">{value}</div>
    </div>
  );
};

// =========================================================
// Streamlit Alerts (Info, Success, Warning, Error)
// =========================================================
export const StAlert: React.FC<{
  type: 'info' | 'success' | 'warning' | 'error';
  children: React.ReactNode;
}> = ({ type, children }) => {
  const alertClasses = {
    info: 'st-alert-info',
    success: 'st-alert-success',
    warning: 'st-alert-warning',
    error: 'st-alert-error',
  }[type];

  const Icon = {
    info: Info,
    success: CheckCircle2,
    warning: AlertTriangle,
    error: XCircle,
  }[type];

  return (
    <div className={`${alertClasses} flex items-start space-x-2.5 my-2.5`}>
      <Icon className="h-4 w-4 mt-0.5 shrink-0" />
      <div className="flex-1 text-xs leading-relaxed whitespace-pre-line">{children}</div>
    </div>
  );
};

// =========================================================
// Streamlit Selectbox
// =========================================================
export const StSelect: React.FC<{
  label?: string;
  value: string | number;
  onChange: (val: string) => void;
  options: { label: string; value: string | number }[] | string[];
  disabled?: boolean;
}> = ({ label, value, onChange, options, disabled = false }) => {
  return (
    <div className="my-2">
      {label && <label className="block text-xs text-[var(--text-primary)] mb-1 font-medium">{label}</label>}
      <select
        value={String(value)}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="st-select disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {options.map((opt) => {
          const optVal = typeof opt === 'object' ? String(opt.value) : opt;
          const optLabel = typeof opt === 'object' ? opt.label : opt;
          return (
            <option key={optVal} value={optVal}>
              {optLabel}
            </option>
          );
        })}
      </select>
    </div>
  );
};

// =========================================================
// Streamlit Slider
// =========================================================
export const StSlider: React.FC<{
  label: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (val: number) => void;
  unit?: string;
}> = ({ label, min, max, step = 1, value, onChange, unit = '' }) => {
  return (
    <div className="my-2.5">
      <div className="flex items-center justify-between text-xs mb-1">
        <label className="text-[var(--text-primary)] font-medium">{label}</label>
        <span className="font-mono text-xs font-semibold" style={{ color: 'var(--accent)' }}>
          {value}
          {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer"
        style={{
          backgroundColor: 'var(--border)',
          accentColor: 'var(--accent)',
        }}
      />
    </div>
  );
};

// =========================================================
// Streamlit Radio Group
// =========================================================
export const StRadio: React.FC<{
  label?: string;
  options: string[];
  value: string;
  onChange: (val: string) => void;
}> = ({ label, options, value, onChange }) => {
  return (
    <div className="my-2">
      {label && <label className="block text-xs text-[var(--text-primary)] mb-1 font-medium">{label}</label>}
      <div className="flex items-center space-x-5 py-1">
        {options.map((opt) => (
          <label key={opt} className="flex items-center space-x-2 text-xs cursor-pointer select-none">
            <input
              type="radio"
              name={label || 'radio-group'}
              checked={value === opt}
              onChange={() => onChange(opt)}
              style={{ accentColor: 'var(--accent)' }}
              className="h-3.5 w-3.5"
            />
            <span style={{ color: 'var(--text-primary)' }}>{opt}</span>
          </label>
        ))}
      </div>
    </div>
  );
};

// =========================================================
// Streamlit Multiselect
// =========================================================
export const StMultiselect: React.FC<{
  label: string;
  options: string[];
  selected: string[];
  onChange: (val: string[]) => void;
}> = ({ label, options, selected, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOption = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((item) => item !== opt));
    } else {
      onChange([...selected, opt]);
    }
  };

  return (
    <div className="my-2 relative">
      <label className="block text-xs text-[var(--text-primary)] mb-1 font-medium">{label}</label>

      {/* Multiselect box */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="st-select min-h-[38px] flex flex-wrap items-center gap-1.5 cursor-pointer"
      >
        {selected.length === 0 ? (
          <span className="text-xs text-[var(--text-muted)]">Choose an option...</span>
        ) : (
          selected.map((item) => (
            <span
              key={item}
              className="inline-flex items-center space-x-1 rounded px-2 py-0.5 text-xs font-medium"
              style={{
                backgroundColor: 'var(--sidebar-bg)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              <span>{item}</span>
              <X
                className="h-3 w-3 cursor-pointer hover:text-red-400"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleOption(item);
                }}
              />
            </span>
          ))
        )}
      </div>

      {/* Dropdown Options */}
      {isOpen && (
        <div
          className="absolute z-20 mt-1 max-h-48 w-full overflow-y-auto rounded-md shadow-lg border p-1"
          style={{
            backgroundColor: 'var(--surface)',
            borderColor: 'var(--border)',
          }}
        >
          {options.map((opt) => {
            const isSelected = selected.includes(opt);
            return (
              <div
                key={opt}
                onClick={() => toggleOption(opt)}
                className={`flex items-center justify-between px-3 py-1.5 text-xs rounded cursor-pointer transition-colors ${
                  isSelected ? 'font-semibold' : ''
                }`}
                style={{
                  backgroundColor: isSelected ? 'rgba(255, 75, 75, 0.1)' : 'transparent',
                  color: isSelected ? 'var(--accent)' : 'var(--text-primary)',
                }}
              >
                <span>{opt}</span>
                {isSelected && <span className="text-[10px]">✓</span>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// =========================================================
// Streamlit Expander (Accordion)
// =========================================================
export const StExpander: React.FC<{
  title: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
}> = ({ title, defaultExpanded = false, children }) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div
      className="rounded-lg border my-3 overflow-hidden"
      style={{
        backgroundColor: 'var(--surface)',
        borderColor: 'var(--border)',
      }}
    >
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-medium transition-colors select-none text-left"
        style={{
          backgroundColor: 'var(--sidebar-bg)',
          color: 'var(--text-primary)',
        }}
      >
        <span>{title}</span>
        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>

      {isExpanded && <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>{children}</div>}
    </div>
  );
};

// =========================================================
// Streamlit Tabs
// =========================================================
export const StTabs: React.FC<{
  tabs: string[];
  activeTab: string;
  onChange: (tab: string) => void;
}> = ({ tabs, activeTab, onChange }) => {
  return (
    <div className="flex border-b my-3" style={{ borderColor: 'var(--border)' }}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab;
        return (
          <button
            key={tab}
            type="button"
            onClick={() => onChange(tab)}
            className="px-4 py-2 text-xs font-medium transition-all relative border-b-2"
            style={{
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              borderColor: isActive ? 'var(--accent)' : 'transparent',
              marginBottom: '-1px',
            }}
          >
            {tab}
          </button>
        );
      })}
    </div>
  );
};
