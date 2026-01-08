'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getAccounts, getDrafts } from '@/lib/api'

export default function Dashboard() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [pendingDrafts, setPendingDrafts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
    const interval = setInterval(loadDashboardData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadDashboardData = async () => {
    try {
      const [accountsRes, draftsRes] = await Promise.all([
        getAccounts(),
        getDrafts({ status: 'pending' }),
      ])
      setAccounts(accountsRes.data.accounts || [])
      setPendingDrafts(draftsRes.data.drafts || [])
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalKarma = accounts.reduce((sum, acc) => sum + (acc.total_karma || 0), 0)
  const activeAccounts = accounts.filter(acc => acc.active).length

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reddit-orange"></div>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Overview of your Reddit Assistant accounts and activity
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            href="/accounts/new"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-reddit-orange hover:bg-reddit-orange/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-reddit-orange"
          >
            Add Account
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Active Accounts</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{activeAccounts}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Pending Drafts</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{pendingDrafts.length}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Total Karma</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{totalKarma}</dd>
          </div>
        </div>
      </div>

      {/* Pending Drafts */}
      {pendingDrafts.length > 0 && (
        <div className="mt-8">
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  You have <strong>{pendingDrafts.length}</strong> pending draft(s) awaiting approval.{' '}
                  <Link href="/drafts" className="font-medium underline">
                    Review now
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Accounts List */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Your Accounts</h2>
        {accounts.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No accounts</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by adding your first Reddit account.</p>
            <div className="mt-6">
              <Link
                href="/accounts/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-reddit-orange hover:bg-reddit-orange/90"
              >
                Add Account
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {accounts.map((account) => (
              <Link
                key={account.id}
                href={`/accounts/${account.id}`}
                className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-reddit-orange hover:shadow-md transition-all"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">u/{account.reddit_username}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {account.total_karma || 0} karma
                    </p>
                    <div className="mt-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          account.active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {account.active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
