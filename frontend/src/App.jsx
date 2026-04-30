import React, { useState } from 'react';
import axios from 'axios';
import { Send, UploadCloud, FileText, Settings, Image as ImageIcon, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

function App() {
  const [formData, setFormData] = useState({
    topic: '',
    prompt: ''
  });
  const [image, setImage] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setImage(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('vLLM이 포스팅을 생성하고 네이버에 등록 중입니다...');

    const data = new FormData();
    data.append('topic', formData.topic);
    data.append('prompt', formData.prompt);
    if (image) {
      data.append('image', image);
    }

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
      const response = await axios.post(`${API_BASE_URL}/api/post`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setStatus('success');
      setMessage(response.data.message || '포스팅이 성공적으로 완료되었습니다!');
    } catch (error) {
      setStatus('error');
      setMessage(error.response?.data?.message || '포스팅 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8 font-sans selection:bg-indigo-500/30">
      <div className="w-full max-w-3xl space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 bg-indigo-500/10 rounded-2xl mb-4 border border-indigo-500/20">
            <Send className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AutoBlog
          </h1>
          <p className="text-slate-400 text-lg">vLLM 기반 네이버 블로그 자동 포스팅 시스템</p>
        </div>

        {/* Main Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-8">
            

            
            {/* Topic Input */}
            <div className="space-y-3">
              <label className="flex items-center space-x-2 text-sm font-medium text-slate-300">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>포스팅 주제</span>
              </label>
              <input
                type="text"
                name="topic"
                value={formData.topic}
                onChange={handleChange}
                placeholder="예: 2026년 인공지능 트렌드 분석"
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all placeholder:text-slate-500"
                required
              />
            </div>

            {/* Prompt Input */}
            <div className="space-y-3">
              <label className="flex items-center space-x-2 text-sm font-medium text-slate-300">
                <Settings className="w-4 h-4 text-purple-400" />
                <span>세부 프롬프트 (vLLM 지시사항)</span>
              </label>
              <textarea
                name="prompt"
                value={formData.prompt}
                onChange={handleChange}
                placeholder="전문적이고 친근한 블로거 말투로 작성해줘. 서론, 본론, 결론으로 나누고 핵심 키워드를 강조해줘."
                rows="4"
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all placeholder:text-slate-500 resize-none"
                required
              />
            </div>

            {/* Image Upload */}
            <div className="space-y-3">
              <label className="flex items-center space-x-2 text-sm font-medium text-slate-300">
                <ImageIcon className="w-4 h-4 text-pink-400" />
                <span>첨부 이미지</span>
              </label>
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl blur opacity-25 group-hover:opacity-40 transition duration-200"></div>
                <label className="relative flex flex-col items-center justify-center w-full h-32 border-2 border-slate-700 border-dashed rounded-xl cursor-pointer bg-slate-800/80 hover:bg-slate-800 transition-colors">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <UploadCloud className="w-8 h-8 mb-3 text-slate-400 group-hover:text-indigo-400 transition-colors" />
                    <p className="mb-2 text-sm text-slate-400">
                      <span className="font-semibold text-indigo-400">클릭하여 업로드</span> 하거나 드래그 앤 드롭
                    </p>
                    <p className="text-xs text-slate-500">PNG, JPG, GIF (MAX. 10MB)</p>
                  </div>
                  <input type="file" className="hidden" onChange={handleFileChange} accept="image/*" />
                </label>
              </div>
              {image && (
                <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600/50">
                  <span className="text-sm text-slate-300 truncate">{image.name}</span>
                  <button type="button" onClick={() => setImage(null)} className="text-slate-400 hover:text-red-400 transition-colors text-sm">삭제</button>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full relative overflow-hidden group bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3.5 px-4 rounded-xl transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {status === 'loading' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>포스팅 생성 중...</span>
                </>
              ) : (
                <>
                  <span className="relative z-10">자동 포스팅 시작</span>
                  <Send className="w-4 h-4 relative z-10 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Status Message */}
        {status !== 'idle' && (
          <div className={`p-4 rounded-xl border flex items-start space-x-3 transition-all animate-in fade-in slide-in-from-bottom-2 ${
            status === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
            status === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
            'bg-blue-500/10 border-blue-500/20 text-blue-400'
          }`}>
            {status === 'success' && <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />}
            {status === 'error' && <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />}
            {status === 'loading' && <Loader2 className="w-5 h-5 flex-shrink-0 mt-0.5 animate-spin" />}
            <div>
              <h3 className="font-medium">{
                status === 'success' ? '성공' :
                status === 'error' ? '오류' : '처리 중'
              }</h3>
              <p className="text-sm opacity-80 mt-1">{message}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
